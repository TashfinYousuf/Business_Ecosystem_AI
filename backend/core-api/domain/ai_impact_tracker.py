"""
backend/core-api/domain/ai_impact_tracker.py
Tracks deterministic ROI metrics: labor hours saved, debt recovered via AI, and discrepancies caught.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger("AIImpactTracker")

# Deterministic operational baselines for South Asian SME commerce
MINUTES_SAVED_PER_MEMO_OCR = 4.5       # Manual data entry & cross-checking vs instant OCR
MINUTES_SAVED_PER_VOICE_ORDER = 3.0     # Phone call listening + paper ledger recording
HOURLY_LABOR_VALUE_BDT = 150.0          # Estimated average hourly cost of an SME manager/accountant


@dataclass
class ImpactSummary:
    total_hours_saved: float
    total_debt_recovered_bdt: float
    total_math_errors_fixed: int
    estimated_labor_cost_saved_bdt: float
    total_monetary_benefit_bdt: float


class AIImpactTracker:
    def __init__(self, pg_conn_string: str):
        self.pg_conn_string = pg_conn_string

    def _get_db(self):
        return psycopg2.connect(self.pg_conn_string)

    def log_automation_time_saved(
        self,
        org_id: str,
        action_type: str,  # "MEMO_OCR" or "VOICE_ORDER"
        source_id: Optional[str] = None,
        item_count: int = 1,
    ) -> None:
        """Logs manual labor hours saved by automating unstructured memo or voice ingestion."""
        if action_type == "MEMO_OCR":
            minutes = MINUTES_SAVED_PER_MEMO_OCR + (item_count * 0.2)
            desc = f"হাতে লেখা মেমোর স্বয়ংক্রিয় ওসিআর পার্সিং ({item_count} টি আইটেম)"
        elif action_type == "VOICE_ORDER":
            minutes = MINUTES_SAVED_PER_VOICE_ORDER
            desc = "ভয়েস অর্ডারের স্বয়ংক্রিয় স্ট্রাকচার্ড এন্ট্রি"
        else:
            minutes = 2.0
            desc = "স্বয়ংক্রিয় এআই হিসাব সমন্বয়"

        hours = round(minutes / 60.0, 3)
        labor_val = round(hours * HOURLY_LABOR_VALUE_BDT, 2)

        with self._get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO ai_impact_events 
                    (org_id, category, source_reference_id, hours_saved, monetary_value_bdt, description, metadata)
                    VALUES (%s, 'TIME_SAVED', %s, %s, %s, %s, %s);
                    """,
                    (
                        org_id,
                        source_id,
                        hours,
                        labor_val,
                        desc,
                        json.dumps({"action_type": action_type, "minutes_saved": minutes}),
                    ),
                )
                self._refresh_summary_record(cursor, org_id)
                conn.commit()

        logger.info("Logged %s minutes saved for org %s (%s).", minutes, org_id, action_type)

    def log_math_discrepancy_caught(
        self,
        org_id: str,
        source_id: str,
        discrepancy_amount: float,
        details: str,
    ) -> None:
        """Logs calculation error caught in handwritten slip before invoicing."""
        with self._get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO ai_impact_events 
                    (org_id, category, source_reference_id, hours_saved, monetary_value_bdt, description, metadata)
                    VALUES (%s, 'CALCULATION_ERROR_CAUGHT', %s, 0.1, %s, %s, %s);
                    """,
                    (
                        org_id,
                        source_id,
                        discrepancy_amount,
                        f"মেমোর ভুল যোগফল সনাক্ত ও সংশোধন: ৳{discrepancy_amount:,.2f}",
                        json.dumps({"details": details}),
                    ),
                )
                self._refresh_summary_record(cursor, org_id)
                conn.commit()

    def attribute_recovered_due_payment(
        self,
        org_id: str,
        customer_id: str,
        paid_amount: float,
        payment_reference_id: str,
    ) -> bool:
        """
        Checks if customer received an AI WhatsApp reminder within last 14 days.
        If yes, attributes the recovered cash amount to the AI recovery pipeline.
        """
        with self._get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT r.id, r.case_id, r.created_at
                    FROM debt_reminder_logs r
                    JOIN debt_recovery_cases c ON r.case_id = c.id
                    WHERE r.org_id = %s 
                      AND c.customer_id = %s 
                      AND r.status = 'DISPATCHED'
                      AND r.dispatched_at >= NOW() - INTERVAL '14 days'
                    ORDER BY r.dispatched_at DESC
                    LIMIT 1;
                    """,
                    (org_id, customer_id),
                )
                match = cursor.fetchone()

                if match:
                    cursor.execute(
                        """
                        INSERT INTO ai_impact_events 
                        (org_id, category, source_reference_id, hours_saved, monetary_value_bdt, description, metadata)
                        VALUES (%s, 'DEBT_RECOVERED', %s, 0.5, %s, %s, %s);
                        """,
                        (
                            org_id,
                            payment_reference_id,
                            paid_amount,
                            f"হোয়াটসঅ্যাপ রিমাইন্ডারের মাধ্যমে বকেয়া আদায়: ৳{paid_amount:,.2f}",
                            json.dumps({"reminder_id": str(match["id"]), "case_id": str(match["case_id"])}),
                        ),
                    )

                    # Update debt reminder log with collected amount
                    cursor.execute(
                        "UPDATE debt_reminder_logs SET recovered_amount = recovered_amount + %s WHERE id = %s;",
                        (paid_amount, match["id"]),
                    )

                    self._refresh_summary_record(cursor, org_id)
                    conn.commit()
                    logger.info("Successfully attributed ৳%s recovered due to AI reminder for org %s.", paid_amount, org_id)
                    return True

        return False

    def get_summary_metrics(self, org_id: str) -> ImpactSummary:
        """Retrieves or computes holistic AI value summary for the merchant dashboard."""
        with self._get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT 
                        COALESCE(SUM(hours_saved), 0) AS total_hours,
                        COALESCE(SUM(monetary_value_bdt) FILTER (WHERE category = 'DEBT_RECOVERED'), 0) AS debt_recovered,
                        COUNT(id) FILTER (WHERE category = 'CALCULATION_ERROR_CAUGHT') AS errors_fixed,
                        COALESCE(SUM(monetary_value_bdt) FILTER (WHERE category = 'TIME_SAVED'), 0) AS labor_saved
                    FROM ai_impact_events
                    WHERE org_id = %s;
                    """,
                    (org_id,),
                )
                row = cursor.fetchone()

        total_hours = float(row["total_hours"])
        debt_recovered = float(row["debt_recovered"])
        errors_fixed = int(row["errors_fixed"])
        labor_saved = float(row["labor_saved"])
        total_benefit = debt_recovered + labor_saved

        return ImpactSummary(
            total_hours_saved=round(total_hours, 1),
            total_debt_recovered_bdt=round(debt_recovered, 2),
            total_math_errors_fixed=errors_fixed,
            estimated_labor_cost_saved_bdt=round(labor_saved, 2),
            total_monetary_benefit_bdt=round(total_benefit, 2),
        )

    def _refresh_summary_record(self, cursor, org_id: str) -> None:
        """Helper to recompute and cache instant summary table."""
        cursor.execute(
            """
            INSERT INTO ai_impact_summaries (org_id, total_hours_saved, total_debt_recovered_bdt, total_math_errors_fixed, estimated_cost_saved_bdt, last_updated_at)
            SELECT 
                %s,
                COALESCE(SUM(hours_saved), 0),
                COALESCE(SUM(monetary_value_bdt) FILTER (WHERE category = 'DEBT_RECOVERED'), 0),
                COUNT(id) FILTER (WHERE category = 'CALCULATION_ERROR_CAUGHT'),
                COALESCE(SUM(monetary_value_bdt) FILTER (WHERE category = 'TIME_SAVED'), 0),
                NOW()
            FROM ai_impact_events
            WHERE org_id = %s
            ON CONFLICT (org_id) DO UPDATE SET
                total_hours_saved = EXCLUDED.total_hours_saved,
                total_debt_recovered_bdt = EXCLUDED.total_debt_recovered_bdt,
                total_math_errors_fixed = EXCLUDED.total_math_errors_fixed,
                estimated_cost_saved_bdt = EXCLUDED.estimated_cost_saved_bdt,
                last_updated_at = NOW();
            """,
            (org_id, org_id),
        )