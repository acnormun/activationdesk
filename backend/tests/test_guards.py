"""Tests for the request check order: 401 -> 403 -> 404 -> 422."""

from .base import ApiTestCase


class GuardOrderTests(ApiTestCase):
    def test_missing_session_is_401_even_for_forbidden_action(self) -> None:
        response = self.client.post("/accounts/alpha/owner", json={"owner": "X"})
        self.assertEqual(response.status_code, 401)

    def test_role_without_permission_is_403_with_allowed_roles(self) -> None:
        self.login("cshead", "cshead123")
        response = self.client.post("/accounts/alpha/owner", json={"owner": "Dana Reed"})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"]["allowed_roles"], ["onboarding_manager"])

    def test_account_outside_scope_is_404_even_with_permission(self) -> None:
        self.login("finance", "finance123")
        response = self.client.post(
            "/accounts/gamma/customer-blocker/close",
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

    def test_value_evidence_cannot_be_empty(self) -> None:
        self.login("manager", "manager123")
        response = self.client.post("/accounts/alpha/value-evidence", json={"evidence": "   "})
        self.assertEqual(response.status_code, 422)
