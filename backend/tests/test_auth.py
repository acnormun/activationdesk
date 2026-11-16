"""Tests for the demo login flow (Pipeline 0)."""

from .base import ApiTestCase


class AuthTests(ApiTestCase):
    def test_login_success_sets_cookie_and_creates_workspace(self) -> None:
        response = self.login("manager", "manager123")
        data = response.json()
        self.assertIn("activationdesk_session", response.cookies)
        self.assertTrue(data["workspace"]["name"].startswith("Demo workspace"))
        self.assertEqual(data["user"]["role"], "onboarding_manager")

    def test_login_wrong_password_is_401(self) -> None:
        response = self.client.post(
            "/auth/login", json={"username": "manager", "password": "nope"}
        )
        self.assertEqual(response.status_code, 401)

    def test_me_without_session_is_401(self) -> None:
        response = self.client.get("/auth/me")
        self.assertEqual(response.status_code, 401)

    def test_me_with_session_returns_user_and_workspace(self) -> None:
        self.login("finance", "finance123")
        data = self.client.get("/auth/me").json()
        self.assertEqual(data["user"]["username"], "finance")
        self.assertEqual(data["user"]["account_ref"], "beta")

    def test_login_seeds_mock_accounts_for_every_lane(self) -> None:
        self.login("cshead", "cshead123")
        accounts = {a["slug"]: a["status"] for a in self.client.get("/accounts").json()}
        self.assertEqual(set(accounts), {"alpha", "beta", "gamma", "delta", "epsilon"})
        self.assertEqual(accounts["beta"], "waiting_on_customer")
        self.assertEqual(accounts["gamma"], "overdue")
        self.assertEqual(accounts["delta"], "blocked_internal")
        self.assertEqual(accounts["epsilon"], "activated")

    def test_finance_sees_only_own_account(self) -> None:
        self.login("finance", "finance123")
        slugs = [a["slug"] for a in self.client.get("/accounts").json()]
        self.assertEqual(slugs, ["beta"])
