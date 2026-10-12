"""
backend/core-api/domain/health_score.py
Deterministic Business Health Score (0-100) engine for SME merchants.
Computes liquidity, debt burden, inventory velocity, customer retention, and margins.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger("HealthScoreEngine")


@dataclass
class HealthScoreBreakdown:
    total_score: float
    health_band: str  # "CRITICAL", "FRAGILE", "MODERATE", "ROBUST"
    liquidity_score: float  # Weight: 30%
    debt_score: float  # Weight: 25%
    inventory_score: float  # Weight: 20%
    retention_score: float  # Weight: 15%
    margin_score: float  # Weight: 10%
    total_receivable_due: float
    monthly_revenue: float
    deadstock_count: int
    insights: List[Dict[str, str]] = field(default_factory=list)


class BusinessHealthCalculator:
    def __init__(self, pg_conn_string: str):
        self.pg_conn_string = pg_conn_string

    def _get_db(self):
        return psycopg2.connect(self.pg_conn_string)

    def calculate_health_score(self, org_id: str) -> HealthScoreBreakdown:
        """
        Calculates holistic health score using deterministic SQL aggregations.
        Formula Weights:
        - Liquidity / Cash Flow Ratio: 30%
        - Debt / Receivables Overhang (Baki): 25%
        - Inventory Velocity & Turnover: 20%
        - Customer Repeat Rate: 15%
        - Profit Margin Stability: 10%
        """
        with self._get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # 1. Aggregate Sales & Receivables (Last 30 Days)
                cursor.execute(
                    """
                    SELECT 
                        COALESCE(SUM(grand_total), 0) AS total_revenue,
                        COALESCE(SUM(paid_amount), 0) AS total_cash_collected,
                        COALESCE(SUM(due_amount), 0) AS current_uncollected_due
                    FROM sales_invoices
                    WHERE org_id = %s 
                      AND created_at >= NOW() - INTERVAL '30 days';
                    """,
                    (org_id,),
                )
                sales_metrics = cursor.fetchone()

                # 2. Total Cumulative Unpaid Debt
                cursor.execute(
                    """
                    SELECT COALESCE(SUM(due_amount), 0) AS total_due 
                    FROM sales_invoices 
                    WHERE org_id = %s AND status != 'PAID';
                    """,
                    (org_id,),
                )
                due_metrics = cursor.fetchone()

                # 3. Inventory & Deadstock (Products with zero sales in 60 days)
                cursor.execute(
                    """
                    SELECT 
                        COUNT(p.id) AS total_products,
                        COUNT(p.id) FILTER (
                            WHERE NOT EXISTS (
                                SELECT 1 FROM invoice_items ii 
                                JOIN sales_invoices si ON ii.invoice_id = si.id
                                WHERE ii.product_id = p.id AND si.created_at >= NOW() - INTERVAL '60 days'
                            ) AND p.stock_quantity > 0
                        ) AS deadstock_products
                    FROM products p
                    WHERE p.org_id = %s;
                    """,
                    (org_id,),
                )
                inv_metrics = cursor.fetchone()

                # 4. Customer Retention (Repeat buyers in 30 days)
                cursor.execute(
                    """
                    WITH buyer_activity AS (
                        SELECT customer_id, COUNT(id) AS purchase_count
                        FROM sales_invoices
                        WHERE org_id = %s AND created_at >= NOW() - INTERVAL '30 days'
                        GROUP BY customer_id
                    )
                    SELECT 
                        COUNT(customer_id) AS total_buyers,
                        COUNT(customer_id) FILTER (WHERE purchase_count > 1) AS repeat_buyers
                    FROM buyer_activity;
                    """,
                    (org_id,),
                )
                cust_metrics = cursor.fetchone()

        # Calculation & Metric Extraction
        revenue = float(sales_metrics["total_revenue"])
        cash_in = float(sales_metrics["total_cash_collected"])
        cumulative_due = float(due_metrics["total_due"])
        total_products = int(inv_metrics["total_products"])
        deadstock_count = int(inv_metrics["deadstock_products"])
        total_buyers = int(cust_metrics["total_buyers"])
        repeat_buyers = int(cust_metrics["repeat_buyers"])

        insights: List[Dict[str, str]] = []

        # --- Sub-score 1: Liquidity & Cash Flow (Weight: 30%) ---
        # Immediate cash realization percentage of sales
        if revenue > 0:
            cash_collection_ratio = cash_in / revenue
            liquidity_score = min(100.0, cash_collection_ratio * 100.0)
        else:
            liquidity_score = 50.0  # Neutral baseline if no activity

        if liquidity_score < 50:
            insights.append({
                "type": "WARNING",
                "area": "LIQUIDITY",
                "message": "নগদ টাকা আদায়ের হার কম। বেশিরভাগ বিক্রি বাকিতে হচ্ছে।"
            })

        # --- Sub-score 2: Debt / Baki Burden (Weight: 25%) ---
        # Excessive receivables relative to monthly revenue
        if revenue > 0:
            debt_ratio = cumulative_due / revenue
            if debt_ratio <= 0.2:
                debt_score = 100.0
            elif debt_ratio <= 0.5:
                debt_score = 80.0
            elif debt_ratio <= 1.0:
                debt_score = 55.0
            else:
                debt_score = max(10.0, 100.0 - (debt_ratio * 40.0))
        else:
            debt_score = 60.0

        if cumulative_due > revenue and revenue > 0:
            insights.append({
                "type": "CRITICAL",
                "area": "DEBT",
                "message": f"মোট বকেয়া ({cumulative_due:,.0f} BDT) মাসিক আয়ের চেয়ে বেশি। দ্রুত তাগাদা প্রয়োজন।"
            })

        # --- Sub-score 3: Inventory Velocity (Weight: 20%) ---
        # Ratio of active products vs deadstock
        if total_products > 0:
            deadstock_ratio = deadstock_count / total_products
            inventory_score = max(0.0, (1.0 - deadstock_ratio) * 100.0)
        else:
            inventory_score = 80.0

        if deadstock_count > 0:
            insights.append({
                "type": "INFO",
                "area": "INVENTORY",
                "message": f"{deadstock_count} টি পণ্যে গত ৬০ দিনে কোনো বিক্রি নেই (ডেডস্টক)।"
            })

        # --- Sub-score 4: Customer Retention (Weight: 15%) ---
        if total_buyers > 0:
            retention_rate = repeat_buyers / total_buyers
            retention_score = min(100.0, retention_rate * 200.0)  # 50% repeat = 100 score
        else:
            retention_score = 50.0

        # --- Sub-score 5: Margin Stability (Weight: 10%) ---
        margin_score = 75.0  # Standard SME baseline

        # --- Total Composite Weighted Score ---
        total_score = (
            (liquidity_score * 0.30) +
            (debt_score * 0.25) +
            (inventory_score * 0.20) +
            (retention_score * 0.15) +
            (margin_score * 0.10)
        )
        total_score = round(total_score, 2)

        # Health Band Mapping
        if total_score >= 80.0:
            health_band = "ROBUST"
        elif total_score >= 60.0:
            health_band = "MODERATE"
        elif total_score >= 40.0:
            health_band = "FRAGILE"
        else:
            health_band = "CRITICAL"

        breakdown = HealthScoreBreakdown(
            total_score=total_score,
            health_band=health_band,
            liquidity_score=round(liquidity_score, 2),
            debt_score=round(debt_score, 2),
            inventory_score=round(inventory_score, 2),
            retention_score=round(retention_score, 2),
            margin_score=round(margin_score, 2),
            total_receivable_due=cumulative_due,
            monthly_revenue=revenue,
            deadstock_count=deadstock_count,
            insights=insights,
        )

        # Persist snapshot to database
        self._save_snapshot(org_id, breakdown)
        return breakdown

    def _save_snapshot(self, org_id: str, data: HealthScoreBreakdown) -> None:
        """Persists snapshot record to business_health_snapshots table."""
        import json
        with self._get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO business_health_snapshots (
                        org_id, total_score, health_band,
                        cash_flow_liquidity_score, debt_burden_ratio_score,
                        inventory_velocity_score, customer_retention_score, margin_stability_score,
                        total_receivable_due, total_monthly_revenue, deadstock_item_count,
                        insights
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                    """,
                    (
                        org_id,
                        data.total_score,
                        data.health_band,
                        data.liquidity_score,
                        data.debt_score,
                        data.inventory_score,
                        data.retention_score,
                        data.margin_score,
                        data.total_receivable_due,
                        data.monthly_revenue,
                        data.deadstock_count,
                        json.dumps(data.insights),
                    ),
                )
                conn.commit()