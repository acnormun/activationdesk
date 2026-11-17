"""Tests for writes: single transaction, history and domain recalculation."""

from datetime import date, timedelta

from .base import ApiTestCase

EVIDENCE = {
    "approved_by": "Morgan Lee",
    "invoice_ref": "INV-2041",
    "via_agreed_workflow": True,
    "approved_at": str(date.today()),
    "recorded_by": "Dana Reed",
}


class ActionTests(ApiTestCase):
    def test_assign_owner_records_history_and_recalculates(self) -> None:
        self.login("manager", "manager123")
        response = self.client.post("/accounts/epsilon/owner", json={"owner": "Dana Reed"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["owner"], "Dana Reed")
        detail = self.client.get("/accounts/epsilon").json()
        pairs = [(h["action"], h["actor_role"]) for h in detail["history"]]
        self.assertIn(("assign_owner", "onboarding_manager"), pairs)

    def test_value_evidence_activates_the_account(self) -> None:
        self.login("manager", "manager123")
        response = self.client.post(
            "/accounts/alpha/value-evidence",
            json=EVIDENCE,
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["status"], "activated")

    def test_future_evidence_approval_is_rejected(self) -> None:
        self.login("manager", "manager123")
        response = self.client.post(
            "/accounts/alpha/value-evidence",
            json={**EVIDENCE, "approved_at": str(date.today() + timedelta(days=1))},
        )
        self.assertEqual(response.status_code, 422, response.text)
        self.assertIn("in the future", response.json()["detail"])

    def test_evidence_without_workflow_confirmation_is_rejected(self) -> None:
        self.login("manager", "manager123")
        response = self.client.post(
            "/accounts/alpha/value-evidence",
            json={**EVIDENCE, "via_agreed_workflow": False},
        )
        self.assertEqual(response.status_code, 422, response.text)
        self.assertIn("agreed workflow", response.json()["detail"])

    def test_second_evidence_is_rejected(self) -> None:
        self.login("manager", "manager123")
        first = self.client.post("/accounts/alpha/value-evidence", json=EVIDENCE)
        self.assertEqual(first.status_code, 200, first.text)
        second = self.client.post("/accounts/alpha/value-evidence", json=EVIDENCE)
        self.assertEqual(second.status_code, 422)
        self.assertEqual(
            second.json()["detail"],
            "Account is activated: no further intervention is allowed.",
        )

    def test_activated_account_rejects_further_changes(self) -> None:
        self.login("manager", "manager123")
        response = self.client.post("/accounts/gamma/owner", json={"owner": "Someone"})
        self.assertEqual(response.status_code, 422)
        self.assertIn("activated", response.json()["detail"])

    def test_closing_internal_blocker_recalculates_status(self) -> None:
        self.login("manager", "manager123")
        response = self.client.post("/accounts/alpha/internal-blocker/close")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "on_track")

    def test_close_customer_blocker_records_finance_role(self) -> None:
        self.login("finance", "finance123")
        response = self.client.post(
            "/accounts/beta/customer-blocker/close",
            json={"customer_update": "Client confirmed the data feed."},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "on_track")
        detail = self.client.get("/accounts/beta").json()
        pairs = [(h["action"], h["actor_role"]) for h in detail["history"]]
        self.assertIn(("close_customer_blocker", "client_finance"), pairs)
