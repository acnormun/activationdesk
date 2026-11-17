"""Tests for the request check order: 401 -> 404 -> 422."""

from .base import ApiTestCase


class GuardOrderTests(ApiTestCase):
    def test_missing_session_is_401_even_for_forbidden_action(self) -> None:
        response = self.client.post("/accounts/alpha/owner", json={"owner": "X"})
        self.assertEqual(response.status_code, 401)

    def test_unknown_account_is_404(self) -> None:
        self.login("manager", "manager123")
        response = self.client.post(
            "/accounts/ghost/customer-blocker/close",
            json={"customer_update": "Client confirmed."},
        )
        self.assertEqual(response.status_code, 404)

    def test_next_action_without_follow_up_is_422_with_reason(self) -> None:
        self.login("manager", "manager123")
        response = self.client.post(
            "/accounts/alpha/next-action", json={"next_action": "Call the client"}
        )
        self.assertEqual(response.status_code, 422)
        self.assertIn("follow-up date", response.json()["detail"])

    def test_target_date_before_start_is_422(self) -> None:
        self.login("manager", "manager123")
        response = self.client.post(
            "/accounts/alpha/target-date", json={"target_date": "2020-01-01"}
        )
        self.assertEqual(response.status_code, 422)
        self.assertIn("start date", response.json()["detail"])

    def test_value_evidence_missing_fields_is_422(self) -> None:
        self.login("manager", "manager123")
        response = self.client.post(
            "/accounts/alpha/value-evidence", json={"approved_by": "Morgan Lee"}
        )
        self.assertEqual(response.status_code, 422)
