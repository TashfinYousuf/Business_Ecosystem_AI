"""
backend/agent-runtime/runtime.py
Durable Agent Execution Runtime with Human-in-the-Loop (HITL) Gate.
Supports execution state checkpointing, suspension, and resumption.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor

from tools import tool_registry

logger = logging.getLogger("DurableRuntime")


@dataclass
class WorkflowStep:
    tool_name: str
    params: Dict[str, Any]
    summary: str


class DurableAgentRuntime:
    def __init__(self, pg_conn_string: str):
        self.pg_conn_string = pg_conn_string
        self.tools = tool_registry

    def _get_db(self):
        return psycopg2.connect(self.pg_conn_string)

    def start_workflow(
        self,
        org_id: str,
        workflow_name: str,
        plan: List[WorkflowStep],
        initial_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Initiates and runs steps until completion or until a human-gate triggers suspension.
        """
        context = initial_context or {}
        serialized_plan = [
            {"tool_name": step.tool_name, "params": step.params, "summary": step.summary}
            for step in plan
        ]

        with self._get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # 1. Initialize workflow execution record
                cursor.execute(
                    """
                    INSERT INTO agent_executions (org_id, workflow_name, status, current_step, state_payload)
                    VALUES (%s, %s, 'RUNNING', 1, %s)
                    RETURNING id;
                    """,
                    (org_id, workflow_name, json.dumps({"plan": serialized_plan, "context": context})),
                )
                execution_id = cursor.fetchone()["id"]
                conn.commit()

        return self._execute_from_step(execution_id, org_id, step_index=0)

    def _execute_from_step(self, execution_id: str, org_id: str, step_index: int) -> Dict[str, Any]:
        """Iterates through planned steps, executing or suspending on approval gates."""
        with self._get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT state_payload FROM agent_executions WHERE id = %s;",
                    (execution_id,),
                )
                record = cursor.fetchone()
                state = record["state_payload"]
                plan = state["plan"]
                context = state["context"]

        while step_index < len(plan):
            current_task = plan[step_index]
            tool_name = current_task["tool_name"]
            tool_params = current_task["params"]
            tool_summary = current_task["summary"]

            tool_def = self.tools.get(tool_name)
            if not tool_def:
                raise ValueError(f"Unknown tool requested by agent: {tool_name}")

            # Check if this tool requires human approval gate
            if tool_def.requires_approval:
                logger.info("Human Gate Triggered for tool '%s'. Suspending execution %s.", tool_name, execution_id)
                approval_id = self._suspend_for_approval(
                    execution_id=execution_id,
                    org_id=org_id,
                    step_index=step_index,
                    action_type=tool_name,
                    summary=tool_summary,
                    params=tool_params,
                    risk_level=tool_def.risk_level,
                )
                return {
                    "execution_id": str(execution_id),
                    "status": "SUSPENDED_AWAITING_APPROVAL",
                    "approval_id": str(approval_id),
                    "action_required": tool_summary,
                    "risk_level": tool_def.risk_level,
                }

            # Execute autonomous tool safely
            try:
                result = tool_def.handler(tool_params)
                context[f"step_{step_index}_result"] = result
                step_index += 1
                self._checkpoint_progress(execution_id, step_index, context)
            except Exception as e:
                logger.error("Step %d execution failed: %s", step_index, str(e))
                self._mark_failed(execution_id, str(e))
                return {"execution_id": str(execution_id), "status": "FAILED", "error": str(e)}

        # Completed all steps successfully
        self._mark_completed(execution_id)
        return {"execution_id": str(execution_id), "status": "COMPLETED", "context": context}

    def _suspend_for_approval(
        self,
        execution_id: str,
        org_id: str,
        step_index: int,
        action_type: str,
        summary: str,
        params: Dict[str, Any],
        risk_level: str,
    ) -> str:
        """Suspends execution and creates approval gate request."""
        with self._get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    UPDATE agent_executions 
                    SET status = 'SUSPENDED_AWAITING_APPROVAL', current_step = %s, updated_at = NOW()
                    WHERE id = %s;
                    """,
                    (step_index + 1, execution_id),
                )

                cursor.execute(
                    """
                    INSERT INTO agent_approval_requests (execution_id, org_id, action_type, action_summary, parameters, risk_level)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id;
                    """,
                    (execution_id, org_id, action_type, summary, json.dumps(params), risk_level),
                )
                approval_id = cursor.fetchone()["id"]
                conn.commit()
                return approval_id

    def resolve_approval_and_resume(
        self,
        approval_id: str,
        decision: str,  # "APPROVED" or "REJECTED"
        user_id: str,
        note: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Merchant resolves human approval gate. If approved, execution resumes from the paused step.
        """
        with self._get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT a.id, a.execution_id, a.org_id, a.action_type, a.parameters, a.status, e.current_step
                    FROM agent_approval_requests a
                    JOIN agent_executions e ON a.execution_id = e.id
                    WHERE a.id = %s;
                    """,
                    (approval_id,),
                )
                req = cursor.fetchone()
                if not req or req["status"] != "PENDING":
                    raise ValueError("Approval request not found or already finalized.")

                execution_id = req["execution_id"]
                step_index = req["current_step"] - 1

                # Update approval request status
                cursor.execute(
                    """
                    UPDATE agent_approval_requests 
                    SET status = %s, resolved_at = NOW(), resolved_by = %s, resolution_note = %s
                    WHERE id = %s;
                    """,
                    (decision, user_id, note, approval_id),
                )

                if decision == "REJECTED":
                    cursor.execute(
                        "UPDATE agent_executions SET status = 'REJECTED', updated_at = NOW() WHERE id = %s;",
                        (execution_id,),
                    )
                    conn.commit()
                    return {"execution_id": str(execution_id), "status": "REJECTED"}

                cursor.execute(
                    "UPDATE agent_executions SET status = 'RESUMED', updated_at = NOW() WHERE id = %s;",
                    (execution_id,),
                )
                conn.commit()

        # Step approved: execute the gated tool and resume subsequent steps
        tool_def = self.tools.get(req["action_type"])
        tool_params = req["parameters"]
        logger.info("Executing approved gate action '%s' for run %s", req["action_type"], execution_id)
        
        # Execute gated action
        _ = tool_def.handler(tool_params)

        # Resume remaining workflow
        return self._execute_from_step(execution_id, req["org_id"], step_index=step_index + 1)

    def _checkpoint_progress(self, execution_id: str, next_step: int, context: Dict[str, Any]) -> None:
        """Saves intermediate execution progress to database."""
        with self._get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE agent_executions 
                    SET current_step = %s, state_payload = jsonb_set(state_payload, '{context}', %s::jsonb), updated_at = NOW()
                    WHERE id = %s;
                    """,
                    (next_step + 1, json.dumps(context), execution_id),
                )
                conn.commit()

    def _mark_completed(self, execution_id: str) -> None:
        with self._get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE agent_executions SET status = 'COMPLETED', updated_at = NOW() WHERE id = %s;",
                    (execution_id,),
                )
                conn.commit()

    def _mark_failed(self, execution_id: str, error_msg: str) -> None:
        with self._get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE agent_executions SET status = 'FAILED', error_message = %s, updated_at = NOW() WHERE id = %s;",
                    (error_msg, execution_id),
                )
                conn.commit()