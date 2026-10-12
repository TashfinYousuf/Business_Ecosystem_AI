"""
backend/core-api/domain/debt_recovery.py
Automated SME Debt Recovery & Persuasive WhatsApp Engine.
Performs aging analysis, tone selection, and queues messages to the Human Gate.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger("DebtRecoveryEngine")

PROMPT_TONE_SYSTEM = """
You are Trade Wolf OS Bengali Communication Assistant for SME merchants.
Your role is to draft a polite, persuasive, yet professional payment reminder message in Bengali for WhatsApp.
Keep it natural, respectful, and culturally appropriate for Bangladeshi shopkeepers and wholesale buyers.

Tone Guidelines:
- GENTLE (1-15 days overdue): Friendly check-in, thank them for their business, soft reminder.
- MODERATE (16-30 days overdue): Professional ledger reconciliation tone, requesting payment this week.
- FIRM (31+ days overdue): Clear and direct reminder mentioning next shipment clearance or account freezing.

Input provided:
- Merchant Name: {merchant_name}
- Customer Name: {customer_name}
- Total Due: {due_amount} BDT
- Oldest Invoice Age: {days_overdue} days
- Tone: {tone}

Output ONLY the final WhatsApp message text in clear, clean Bengali.
"""


@dataclass
class DebtCaseAnalysis:
    customer_id: str
    customer_name: str
    phone_number: str
    total_due: float
    oldest_due_date: str
    days_overdue: int
    aging_bucket: str
    recommended_tone: str


class DebtRecoveryPipeline:
    def __init__(self, pg_conn_string: str, ai_gateway=None):
        self.pg_conn_string = pg_conn_string
        self.gateway = ai_gateway

    def _get_db(self):
        return psycopg2.connect(self.pg_conn_string)

    def scan_and_analyze_overdue_debts(self, org_id: str) -> List[DebtCaseAnalysis]:
        """
        Scans all customers with unpaid invoices and classifies into aging buckets:
        - 1_15_DAYS: Gentle
        - 16_30_DAYS: Moderate
        - 31_60_DAYS: Firm
        - OVER_60_DAYS: Urgent
        """
        query = """
            SELECT 
                c.id AS customer_id,
                c.name AS customer_name,
                c.phone AS phone_number,
                SUM(si.due_amount) AS total_due,
                MIN(si.due_date) AS oldest_due_date,
                CURRENT_DATE - MIN(si.due_date) AS days_overdue
            FROM sales_invoices si
            JOIN customers c ON si.customer_id = c.id
            WHERE si.org_id = %s 
              AND si.status != 'PAID' 
              AND si.due_amount > 0
              AND si.due_date < CURRENT_DATE
            GROUP BY c.id, c.name, c.phone
            HAVING SUM(si.due_amount) > 0
            ORDER BY days_overdue DESC;
        """

        analyzed_cases: List[DebtCaseAnalysis] = []

        with self._get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, (org_id,))
                rows = cursor.fetchall()

                for row in rows:
                    days = int(row["days_overdue"])
                    if days <= 15:
                        bucket = "1_15_DAYS"
                        tone = "GENTLE"
                    elif days <= 30:
                        bucket = "16_30_DAYS"
                        tone = "MODERATE"
                    elif days <= 60:
                        bucket = "31_60_DAYS"
                        tone = "FIRM"
                    else:
                        bucket = "OVER_60_DAYS"
                        tone = "URGENT"

                    analyzed_cases.append(
                        DebtCaseAnalysis(
                            customer_id=str(row["customer_id"]),
                            customer_name=row["customer_name"],
                            phone_number=row["phone_number"] or "",
                            total_due=float(row["total_due"]),
                            oldest_due_date=str(row["oldest_due_date"]),
                            days_overdue=days,
                            aging_bucket=bucket,
                            recommended_tone=tone,
                        )
                    )

        return analyzed_cases

    async def generate_and_queue_reminder(
        self,
        org_id: str,
        merchant_business_name: str,
        case: DebtCaseAnalysis,
    ) -> Dict[str, Any]:
        """
        Drafts a culturally calibrated WhatsApp message and safely queues it for Human Approval.
        Does NOT dispatch automatically to protect merchant reputation.
        """
        # 1. Draft message content
        if self.gateway:
            prompt = PROMPT_TONE_SYSTEM.format(
                merchant_name=merchant_business_name,
                customer_name=case.customer_name,
                due_amount=f"{case.total_due:,.2f}",
                days_overdue=case.days_overdue,
                tone=case.recommended_tone,
            )
            messages = [{"role": "user", "content": prompt}]
            response = await self.gateway.generate_completion(messages=messages, temperature=0.2)
            drafted_text = response.content.strip()
        else:
            # Deterministic standard template fallback
            if case.recommended_tone == "GENTLE":
                drafted_text = (
                    f"আসসালামু আলাইকুম {case.customer_name} ভাই। {merchant_business_name} থেকে আশা করি ভালো আছেন। "
                    f"আপনার মোট {case.total_due:,.0f} টাকার একটি বকেয়া রয়েছে। সুবিধা মতো সময়ে পরিশোধের ব্যবস্থা নিলে কৃতজ্ঞ থাকব।"
                )
            elif case.recommended_tone == "MODERATE":
                drafted_text = (
                    f"সম্মানিত {case.customer_name}, {merchant_business_name}-এর হিসাবের খাতা অনুযায়ী আপনার {case.total_due:,.0f} টাকা বকেয়া রয়েছে "
                    f"({case.days_overdue} দিন যাবত)। সাপ্তাহিক ক্যাশ ক্লোজিংয়ের সুবিধার্থে অনুগ্রহ করে চলতি সপ্তাহের মধ্যে পরিশোধ করার অনুরোধ করা যাচ্ছে।"
                )
            else:
                drafted_text = (
                    f"জরুরি নোটিশ: {case.customer_name}, আপনার {case.total_due:,.0f} টাকা বকেয়া দীর্ঘ {case.days_overdue} দিন ধরে অনাদায়ী রয়েছে। "
                    f"পরবর্তী চালানের সরবরাহ সচল রাখতে অনুগ্রহ করে জরুরি ভিত্তিতে হিসাবটি ক্লিয়ার করুন।"
                )

        # 2. Persist debt case & reminder in database, link with Human Gate
        with self._get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Upsert case
                cursor.execute(
                    """
                    INSERT INTO debt_recovery_cases 
                    (org_id, customer_id, total_due_amount, oldest_due_date, aging_bucket, risk_level, status)
                    VALUES (%s, %s, %s, %s, %s, %s, 'ACTIVE')
                    ON CONFLICT (id) DO NOTHING
                    RETURNING id;
                    """,
                    (
                        org_id,
                        case.customer_id,
                        case.total_due,
                        case.oldest_due_date,
                        case.aging_bucket,
                        "HIGH" if case.days_overdue > 30 else "MEDIUM",
                    ),
                )
                case_id_row = cursor.fetchone()
                case_id = case_id_row["id"] if case_id_row else None

                # Queue Human Approval Request
                approval_summary = f"Send {case.recommended_tone} WhatsApp payment reminder to {case.customer_name} ({case.phone_number}) for {case.total_due:,.0f} BDT"
                approval_params = {
                    "customer_id": case.customer_id,
                    "customer_name": case.customer_name,
                    "phone": case.phone_number,
                    "total_due": case.total_due,
                    "message_body": drafted_text,
                    "tone": case.recommended_tone,
                }

                cursor.execute(
                    """
                    INSERT INTO agent_approval_requests (execution_id, org_id, action_type, action_summary, parameters, risk_level)
                    VALUES (gen_random_uuid(), %s, 'send_whatsapp_debt_notice', %s, %s, 'MEDIUM')
                    RETURNING id;
                    """,
                    (org_id, approval_summary, json.dumps(approval_params)),
                )
                approval_id = cursor.fetchone()["id"]

                # Log reminder draft
                if case_id:
                    cursor.execute(
                        """
                        INSERT INTO debt_reminder_logs (case_id, org_id, tone, channel, message_body, status, approval_request_id)
                        VALUES (%s, %s, %s, 'WHATSAPP', %s, 'PENDING_APPROVAL', %s);
                        """,
                        (case_id, org_id, case.recommended_tone, drafted_text, approval_id),
                    )

                conn.commit()

        logger.info("Debt reminder drafted & queued for merchant review. Approval ID: %s", approval_id)

        return {
            "status": "QUEUED_FOR_APPROVAL",
            "approval_id": str(approval_id),
            "customer_name": case.customer_name,
            "tone": case.recommended_tone,
            "drafted_message": drafted_text,
        }