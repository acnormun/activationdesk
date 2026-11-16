"""Tests for the Roles and access matrix (10 actions x 3 roles)."""

from .base import ApiTestCase


class RolesAndAccessTests(ApiTestCase):
    def test_matrix_has_10_actions_and_3_roles(self) -> None:
        self.login("manager", "manager123")
        actions = self.client.get("/permissions").json()["actions"]
        self.assertEqual(len(actions), 10)
        matrix = {a["action"]: a for a in actions}
        self.assertTrue(matrix["assign_owner"]["onboarding_manager"])
        self.assertFalse(matrix["assign_owner"]["client_finance"])
        self.assertFalse(matrix["close_customer_blocker"]["onboarding_manager"])
        self.assertTrue(matrix["close_customer_blocker"]["client_finance"])
        self.assertTrue(matrix["view_dashboard"]["cs_head"])
        self.assertFalse(matrix["record_progress"]["cs_head"])

    def test_manager_cannot_close_customer_blocker(self) -> None:
        self.login("manager", "manager123")
        response = self.client.post(
            "/accounts/beta/customer-blocker/close",
            json={"customer_update": "Client said ok."},
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"]["allowed_roles"], ["client_finance"])

    def test_cs_head_is_read_only(self) -> None:
        self.login("cshead", "cshead123")
        self.assertEqual(self.client.get("/accounts").status_code, 200)
        response = self.client.post("/accounts/alpha/progress", json={"note": "Checked in"})
        self.assertEqual(response.status_code, 403)
