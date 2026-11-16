"""Tests for writes: single transaction, history and Pipeline 1 recalculation."""

from .base import ApiTestCase


class ActionTests(ApiTestCase):
    def test_assign_owner_records_history_and_recalculates(self) -> None:
        self.login("manager", "manager123")
        response = self.client.post("/accounts/gamma/owner", json={"owner": "Dana Reed"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["owner"], "Dana Reed")
        detail = self.client.get("/accounts/gamma").json()
        pairs = [(h["action"], h["actor_role"]) for h in detail["history"]]
        self.assertIn(("assign_owner", "onboarding_manager"), pairs)

    def test_value_evidence_activates_the_account(self) -> None:
        self.login("manager", "manager123")
        response = self.client.post(
            "/accounts/alpha/value-evidence",
            json={"evidence": "Dashboard live for the client."},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "activated")

    def test_activated_account_rejects_further_changes(self) -> None:
        self.login("manager", "manager123")
        response = self.client.post("/accounts/epsilon/owner", json={"owner": "Someone"})
        self.assertEqual(response.status_code, 422)
        self.assertIn("activated", response.json()["detail"])

    def test_closing_internal_blocker_recalculates_status(self) -> None:
        self.login("manager", "manager123")
        response = self.client.post("/accounts/delta/internal-blocker/close")
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
