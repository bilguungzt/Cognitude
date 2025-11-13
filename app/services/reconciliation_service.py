"""
Service for reconciling internal LLM costs with external billing data.
"""
import csv
from datetime import datetime
from decimal import Decimal
from typing import Dict, List

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import LLMRequest, ReconciliationReport, Organization
from app.services.alert_service import NotificationService


class ReconciliationService:
    """
    A service to compare internal cost tracking with external invoices.
    """

    def __init__(self, db: Session):
        self.db = db
        self.notification_service = NotificationService(db)

    def run_reconciliation(
        self,
        organization_id: int,
        start_date: datetime,
        end_date: datetime,
        external_source_path: str,
    ):
        """
        Orchestrates the reconciliation process for a given organization.
        """
        # 1. Fetch internal data
        internal_cost = self._fetch_internal_billing_data(
            organization_id, start_date, end_date
        )

        # 2. Fetch external data
        external_cost = self._fetch_external_billing_data(
            external_source_path, start_date, end_date
        )

        # 3. Compare data
        comparison_result = self._compare_data(internal_cost, external_cost)

        # 4. Create report
        report = self._create_reconciliation_report(
            organization_id,
            start_date,
            end_date,
            internal_cost,
            external_cost,
            comparison_result,
        )

        # 5. Send alert if discrepancy is found
        if report.status == "DISCREPANCY_FOUND":
            self.notification_service.send_reconciliation_alert(report)

        return report

    def _fetch_internal_billing_data(
        self, organization_id: int, start_date: datetime, end_date: datetime
    ) -> Decimal:
        """
        Calculates the total cost from the llm_requests table for a given period.
        """
        total_cost = (
            self.db.query(func.sum(LLMRequest.cost_usd))
            .filter(
                LLMRequest.organization_id == organization_id,
                LLMRequest.timestamp >= start_date,
                LLMRequest.timestamp < end_date,
            )
            .scalar()
        )
        return total_cost or Decimal("0.0")

    def _fetch_external_billing_data(
        self, file_path: str, start_date: datetime, end_date: datetime
    ) -> Decimal:
        """
        Parses a CSV file to get the total cost from an external source.
        
        Assumes CSV format: 'Date', 'Cost'
        """
        total_cost = Decimal("0.0")
        with open(file_path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    record_date = datetime.fromisoformat(row["Date"])
                    if start_date <= record_date < end_date:
                        total_cost += Decimal(row["Cost"])
                except (KeyError, ValueError):
                    # Handle malformed rows or missing columns
                    continue
        return total_cost

    def _compare_data(
        self, internal_cost: Decimal, external_cost: Decimal
    ) -> Dict:
        """
        Compares internal and external costs and calculates the variance.
        """
        if external_cost == Decimal("0.0"):
            variance_percent = (
                Decimal("0.0")
                if internal_cost == Decimal("0.0")
                else Decimal("100.0")
            )
        else:
            variance_percent = (
                abs(internal_cost - external_cost) / external_cost
            ) * 100

        variance_usd = abs(internal_cost - external_cost)

        # TODO: Make threshold configurable
        status = (
            "DISCREPANCY_FOUND"
            if variance_percent > 1
            else "SUCCESS"
        )

        return {
            "variance_usd": variance_usd,
            "variance_percent": float(variance_percent),
            "status": status,
        }

    def _create_reconciliation_report(
        self,
        organization_id: int,
        start_date: datetime,
        end_date: datetime,
        internal_cost: Decimal,
        external_cost: Decimal,
        comparison_result: Dict,
    ) -> ReconciliationReport:
        """
        Saves a new ReconciliationReport to the database.
        """
        report = ReconciliationReport(
            organization_id=organization_id,
            start_date=start_date,
            end_date=end_date,
            internal_cost_usd=internal_cost,
            external_cost_usd=external_cost,
            variance_usd=comparison_result["variance_usd"],
            variance_percent=comparison_result["variance_percent"],
            status=comparison_result["status"],
        )
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report