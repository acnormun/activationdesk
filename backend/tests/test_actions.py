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

    def test_close_customer_blocker_records_manager_role(self) -> None:
        self.login("manager", "manager123")
        response = self.client.post(
            "/accounts/beta/customer-blocker/close",
            json={"customer_update": "Client confirmed the data feed."},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "on_track")
        detail = self.client.get("/accounts/beta").json()
        pairs = [(h["action"], h["actor_role"]) for h in detail["history"]]
        self.assertIn(("close_customer_blocker", "onboarding_manager"), pairs)

    def test_open_internal_blocker_with_milestone_records_reference(self) -> None:
        self.login("manager", "manager123")
        response = self.client.post(
            "/accounts/delta/internal-blocker",
            json={
                "description": "Sample mapping blocked the import",
                "milestone": "import",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["internal_blocker_milestone"], "import")
        self.assertEqual(response.json()["status"], "blocked_internal")
        detail = self.client.get("/accounts/delta").json()
        self.assertIn("holds up: import", detail["history"][0]["detail"])

    def test_open_internal_blocker_rejects_unknown_milestone(self) -> None:
        self.login("manager", "manager123")
        response = self.client.post(
            "/accounts/delta/internal-blocker",
            json={"description": "Stuck", "milestone": "go_live"},
        )
        self.assertEqual(response.status_code, 422)
        self.assertIn("Unknown milestone", response.json()["detail"])

    def test_seeded_blockers_reference_their_milestones(self) -> None:
        self.login("manager", "manager123")
        accounts = {a["slug"]: a for a in self.client.get("/accounts").json()}
        self.assertEqual(accounts["alpha"]["internal_blocker_milestone"], "import")
        self.assertEqual(accounts["beta"]["customer_blocker_milestone"], "first_value")
        self.assertEqual(accounts["zeta"]["internal_blocker_milestone"], "first_value")

    def test_close_customer_blocker_clears_milestone_reference(self) -> None:
        self.login("manager", "manager123")
        response = self.client.post(
            "/accounts/beta/customer-blocker/close",
            json={"customer_update": "Client confirmed the data feed."},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()["customer_blocker_milestone"])

    def test_milestone_marked_done_records_fact_and_history(self) -> None:
        self.login("manager", "manager123")
        response = self.client.post("/accounts/delta/milestones/setup")
        self.assertEqual(response.status_code, 200)
        milestones = {m["name"]: m for m in response.json()["activity_milestones"]}
        self.assertTrue(milestones["setup"]["done"])
        self.assertEqual(milestones["setup"]["completed_at"], str(date.today()))
        detail = self.client.get("/accounts/delta").json()
        pairs = [(h["action"], h["actor_role"]) for h in detail["history"]]
        self.assertIn(("update_milestone", "onboarding_manager"), pairs)

    def test_already_done_milestone_is_rejected(self) -> None:
        self.login("manager", "manager123")
        response = self.client.post("/accounts/alpha/milestones/setup")
        self.assertEqual(response.status_code, 422)
        self.assertIn("already done", response.json()["detail"])

    def test_unknown_milestone_is_rejected(self) -> None:
        self.login("manager", "manager123")
        response = self.client.post("/accounts/delta/milestones/go-live")
        self.assertEqual(response.status_code, 422)
        self.assertIn("Unknown activity milestone", response.json()["detail"])

    def test_activated_account_rejects_milestone_update(self) -> None:
        self.login("manager", "manager123")
        response = self.client.post("/accounts/gamma/milestones/training")
        self.assertEqual(response.status_code, 422)
        self.assertIn("activated", response.json()["detail"])

    def test_open_customer_blocker_sets_waiting_on_customer(self) -> None:
        self.login("manager", "manager123")
        response = self.client.post(
            "/accounts/delta/customer-blocker",
            json={
                "description": "Customer needs legal sign-off",
                "milestone": "first_value",
            },
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["customer_blocker"], "Customer needs legal sign-off")
        self.assertEqual(response.json()["customer_blocker_milestone"], "first_value")
        self.assertEqual(response.json()["status"], "waiting_on_customer")

    def test_open_internal_blocker_requires_milestone(self) -> None:
        self.login("manager", "manager123")
        response = self.client.post(
            "/accounts/delta/internal-blocker",
            json={"description": "Stuck without a milestone"},
        )
        self.assertEqual(response.status_code, 422)
        self.assertIn("milestone is required", response.json()["detail"])

    def test_open_customer_blocker_requires_milestone(self) -> None:
        self.login("manager", "manager123")
        response = self.client.post(
            "/accounts/delta/customer-blocker",
            json={"description": "Stuck without a milestone"},
        )
        self.assertEqual(response.status_code, 422)
        self.assertIn("milestone is required", response.json()["detail"])

    def test_close_customer_blocker_marks_history_simulated(self) -> None:
        self.login("manager", "manager123")
        response = self.client.post(
            "/accounts/beta/customer-blocker/close",
            json={"customer_update": "Client confirmed the approval policy."},
        )
        self.assertEqual(response.status_code, 200)
        detail = self.client.get("/accounts/beta").json()
        entry = detail["history"][0]
        self.assertTrue(entry["simulated"])
        self.assertIn("Simulated", entry["detail"])
