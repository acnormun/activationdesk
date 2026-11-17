"""Tests for the week plan endpoint and domain-derived account reads."""

from .base import ApiTestCase


def slugs(entries: list[dict]) -> list[str]:
    return [entry["account_slug"] for entry in entries]


class WeekPlanTests(ApiTestCase):
    def test_seed_covers_every_lane(self) -> None:
        self.login("manager", "manager123")
        response = self.client.get("/plan/week")
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertEqual(data["slots"], 2)
        lanes = data["lanes"]
        self.assertEqual(slugs(lanes["intervention"]), ["alpha", "zeta"])
        self.assertEqual(slugs(lanes["nudge"]), ["beta"])
        self.assertEqual(slugs(lanes["triage"]), ["epsilon"])
        self.assertEqual(slugs(lanes["monitor"]), ["delta"])
        self.assertEqual(slugs(lanes["no_intervention"]), ["gamma"])
        self.assertEqual(lanes["waiting_for_capacity"], [])
        self.assertEqual(data["empty_slots"], 0)
        self.assertEqual(data["message"], "")

    def test_intervention_entry_has_explainable_score(self) -> None:
        self.login("manager", "manager123")
        data = self.client.get("/plan/week").json()
        entry = data["lanes"]["intervention"][0]
        self.assertEqual(entry["account_slug"], "alpha")
        self.assertTrue(entry["reason"])
        total = 0
        for label in ("urgency", "stagnation", "closeness", "followup"):
            component = entry["score"][label]
            self.assertTrue(component["reason"], label)
            total += component["points"]
        self.assertEqual(entry["score_total"], total)

    def test_nudge_entry_has_level_and_no_score(self) -> None:
        self.login("manager", "manager123")
        data = self.client.get("/plan/week").json()
        entry = data["lanes"]["nudge"][0]
        self.assertEqual(entry["nudge_level"], "remind")
        self.assertNotIn("score", entry)

    def test_slots_parameter_changes_empty_slots(self) -> None:
        self.login("manager", "manager123")
        data = self.client.get("/plan/week?slots=1").json()
        self.assertEqual(data["slots"], 1)
        self.assertEqual(data["empty_slots"], 0)

    def test_week_plan_requires_session(self) -> None:
        self.assertEqual(self.client.get("/plan/week").status_code, 401)


class DomainStatusReadTests(ApiTestCase):
    def test_reads_derive_status_and_flags_from_facts(self) -> None:
        self.login("manager", "manager123")
        accounts = {a["slug"]: a for a in self.client.get("/accounts").json()}
        self.assertEqual(accounts["alpha"]["status"], "blocked_internal")
        self.assertEqual(accounts["beta"]["status"], "waiting_on_customer")
        self.assertEqual(accounts["gamma"]["status"], "activated")
        self.assertEqual(accounts["delta"]["status"], "on_track")
        self.assertEqual(accounts["epsilon"]["status"], "overdue")
        self.assertEqual(
            accounts["epsilon"]["flags"], ["no_owner", "no_next_action", "past_target"]
        )
        self.assertEqual(accounts["zeta"]["status"], "blocked_internal")

    def test_detail_exposes_desired_outcome(self) -> None:
        self.login("manager", "manager123")
        detail = self.client.get("/accounts/alpha").json()
        self.assertTrue(detail["account"]["desired_outcome"])
