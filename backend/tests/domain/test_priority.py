"""Seed-case and boundary tests for the weekly priority rules."""

import unittest
from dataclasses import replace
from datetime import timedelta

from app.domain.models import (
    BlockerSide,
    BlockerStatus,
    Evidence,
    Lane,
    MilestoneKind,
    MilestoneStatus,
    NextAction,
    NudgeLevel,
    ResolvedVia,
    Status,
)
from app.domain.priority import (
    deadline_consumption,
    plan_week,
    priority_score,
)
from app.domain.seed import SAMPLE_DAY, account_by_id
from .factories import (
    activity,
    blocker,
    make_account,
    value,
    window_account,
)

D = SAMPLE_DAY


class PlanWeekSeedTests(unittest.TestCase):
    """Case 6: every seeded account lands in its lane with its score."""

    def setUp(self):
        self.plan = plan_week(tuple(account_by_id(a) for a in
                                   ("alpha", "beta", "gamma", "delta", "epsilon", "zeta")), D)

    def _names(self, lane: Lane) -> list[str]:
        return [entry.account.name for entry in self.plan.entries_in_lane(lane)]

    def test_intervention_is_alpha_then_zeta(self):
        self.assertEqual(self._names(Lane.INTERVENTION), ["Alpha Corp", "Zeta Inc"])

    def test_nudge_is_beta_with_remind_and_no_score(self):
        entries = self.plan.nudge
        self.assertEqual(self._names(Lane.NUDGE), ["Beta Ltd"])
        self.assertIs(entries[0].nudge_level, NudgeLevel.REMIND)
        self.assertIsNone(entries[0].score)

    def test_triage_monitor_and_activated_lanes(self):
        self.assertEqual(self._names(Lane.TRIAGE), ["Epsilon GmbH"])
        self.assertEqual(self._names(Lane.MONITOR), ["Delta LLC"])
        self.assertEqual(self._names(Lane.NO_INTERVENTION), ["Gamma SA"])

    def test_alpha_score_breakdown_40_10_20_10(self):
        entry = self.plan.intervention[0]
        breakdown = entry.score
        self.assertEqual(breakdown.urgency.points, 40)
        self.assertEqual(breakdown.stagnation.points, 10)
        self.assertEqual(breakdown.closeness.points, 20)
        self.assertEqual(breakdown.followup.points, 10)
        self.assertEqual(breakdown.total, 80)
        self.assertEqual(breakdown.not_calculated, ())
        self.assertEqual(entry.reason, (
            "Intervention slot 1: score 80 (urgency 40, stagnation 10, "
            "closeness 20, follow-up 10)."
        ))

    def test_zeta_score_breakdown_40_0_20_10(self):
        entry = self.plan.intervention[1]
        breakdown = entry.score
        self.assertEqual(breakdown.urgency.points, 40)
        self.assertEqual(breakdown.stagnation.points, 0)
        self.assertEqual(breakdown.closeness.points, 20)
        self.assertEqual(breakdown.followup.points, 10)
        self.assertEqual(breakdown.total, 70)

    def test_no_empty_slots_on_the_full_seed(self):
        self.assertEqual(self.plan.empty_slots, 0)
        self.assertEqual(self.plan.message, "")


class ActivatingAlphaTests(unittest.TestCase):
    """Case 8: once Alpha is activated, a slot stays empty."""

    def test_activated_alpha_leaves_one_empty_slot(self):
        alpha = account_by_id("alpha")

        resolved = replace(
            alpha.blockers[0],
            status=BlockerStatus.RESOLVED,
            resolved_via=ResolvedVia.INTERNAL_FIX,
            resolved_at=D,
        )
        evidence = Evidence(
            approved_by="Customer finance owner",
            invoice_ref="INV-2091",
            via_agreed_workflow=True,
            approved_at=D,
            recorded_by="Ana",
        )
        value_milestone = alpha.value_milestone
        value_done = replace(
            value_milestone,
            status=MilestoneStatus.DONE,
            completed_at=D,
            evidence=evidence,
        )
        milestones = tuple(
            value_done if m.kind is MilestoneKind.VALUE else m
            for m in alpha.milestones
        )
        activated = replace(alpha, blockers=(resolved,), milestones=milestones)

        from app.domain.status import derive_status
        self.assertIs(derive_status(activated, D).status, Status.ACTIVATED)

        others = tuple(
            account_by_id(a) for a in ("beta", "gamma", "delta", "epsilon", "zeta")
        )
        plan = plan_week((activated,) + others, D)
        self.assertEqual(
            [e.account.name for e in plan.intervention], ["Zeta Inc"]
        )
        self.assertEqual(plan.empty_slots, 1)
        self.assertIn(
            "No other account our team can unblock right now.", plan.message
        )


class NudgeLaneTests(unittest.TestCase):
    """Nudge order: deadline consumption descending, unknown last; nudges
    never take a slot."""

    def _customer_blocked(self, name: str, target, start=D - timedelta(days=14)):
        return make_account(
            id=name.lower(),
            name=name,
            start=start,
            target=target,
            owner="Ana",
            milestones=(value(),),
            blockers=(
                blocker(
                    side=BlockerSide.CUSTOMER,
                    opened_at=D - timedelta(days=4),
                    owner="Customer finance lead",
                ),
            ),
        )

    def test_nudge_order_consumption_desc_then_none_last(self):
        high = self._customer_blocked("High", D + timedelta(days=2))
        mid = self._customer_blocked("Mid", D + timedelta(days=10))
        unknown = self._customer_blocked("Unknown", D + timedelta(days=1), start=None)
        plan = plan_week((unknown, mid, high), D)
        self.assertEqual(
            [e.account.name for e in plan.nudge], ["High", "Mid", "Unknown"]
        )

    def test_nudges_never_take_slots(self):
        only = self._customer_blocked("Only", D + timedelta(days=2))
        plan = plan_week((only,), D, slots=2)
        self.assertEqual(plan.intervention, ())
        self.assertEqual(plan.empty_slots, 2)
        self.assertEqual(len(plan.nudge), 1)


class DeadlineConsumptionTests(unittest.TestCase):
    def test_consumption_exact_fraction(self):
        account = window_account(D, elapsed=14, total=17)
        self.assertAlmostEqual(deadline_consumption(account, D), 14 / 17)

    def test_consumption_none_without_start_date(self):
        account = make_account(id="x", name="X", target=D + timedelta(days=3), start=None)
        self.assertIsNone(deadline_consumption(account, D))

    def test_consumption_none_with_non_positive_window(self):
        account = make_account(
            id="x", name="X",
            target=D - timedelta(days=5), start=D - timedelta(days=5),
        )
        self.assertIsNone(deadline_consumption(account, D))


class UrgencyBoundaryTests(unittest.TestCase):
    """Case 13: exact urgency points at the rule boundaries."""

    def test_urgency_boundaries_by_consumption_and_days_left(self):
        cases = [
            # (elapsed, total, expected points)
            (79, 100, 20),  # consumption 0.79 -> attention
            (80, 100, 40),  # consumption 0.80 -> critical
            (49, 100, 0),   # consumption 0.49 -> comfortable
            (50, 100, 20),  # consumption 0.50 -> attention
            (50, 50, 40),   # days_left 0 -> critical
            (50, 49, 50),   # days_left -1 -> overdue
            (1, 3, 0),      # low consumption, days_left 2 -> comfortable
            (1, 2, 40),     # days_left 1 -> critical
        ]
        for elapsed, total, expected in cases:
            with self.subTest(elapsed=elapsed, total=total):
                account = window_account(D, elapsed=elapsed, total=total)
                breakdown = priority_score(account, D)
                self.assertEqual(breakdown.urgency.points, expected)
                self.assertTrue(breakdown.urgency.calculated)

    def test_urgency_days_only_fallback_without_start_date(self):
        cases = [
            # (target offset from D, expected points)
            (-1, 50),
            (1, 40),
            (5, 0),
        ]
        for offset, expected in cases:
            with self.subTest(offset=offset):
                account = make_account(
                    id="x", name="X",
                    target=D + timedelta(days=offset), start=None,
                )
                breakdown = priority_score(account, D)
                self.assertEqual(breakdown.urgency.points, expected)
                self.assertFalse(breakdown.urgency.calculated)
                self.assertIn("urgency", breakdown.not_calculated)


class StagnationBoundaryTests(unittest.TestCase):
    """Case 14: days since the oldest open internal blocker."""

    def test_stagnation_bands(self):
        cases = [
            (2, 0),
            (3, 10),
            (5, 10),
            (6, 20),
        ]
        for opened_days_ago, expected in cases:
            with self.subTest(opened_days_ago=opened_days_ago):
                account = window_account(
                    D,
                    elapsed=14,
                    total=20,
                    blockers=(
                        blocker(opened_at=D - timedelta(days=opened_days_ago)),
                    ),
                )
                breakdown = priority_score(account, D)
                self.assertEqual(breakdown.stagnation.points, expected)

    def test_stagnation_ignores_customer_and_resolved_blockers(self):
        customer_only = window_account(
            D,
            elapsed=14,
            total=20,
            blockers=(
                blocker(
                    side=BlockerSide.CUSTOMER,
                    opened_at=D - timedelta(days=30),
                ),
            ),
        )
        resolved_only = window_account(
            D,
            elapsed=14,
            total=20,
            blockers=(
                blocker(
                    status=BlockerStatus.RESOLVED,
                    opened_at=D - timedelta(days=30),
                ),
            ),
        )
        self.assertEqual(priority_score(customer_only, D).stagnation.points, 0)
        self.assertEqual(priority_score(resolved_only, D).stagnation.points, 0)

    def test_stagnation_not_calculated_when_opened_at_missing(self):
        account = window_account(
            D, elapsed=14, total=20, blockers=(blocker(opened_at=None),)
        )
        breakdown = priority_score(account, D)
        self.assertEqual(breakdown.stagnation.points, 0)
        self.assertFalse(breakdown.stagnation.calculated)
        self.assertIn("stagnation", breakdown.not_calculated)


class ClosenessBoundaryTests(unittest.TestCase):
    """Case 15: pending ACTIVITY milestones (VALUE never counts)."""

    def test_closeness_by_pending_activities(self):
        cases = [
            (0, 20),
            (1, 10),
            (2, 0),
        ]
        for pending, expected in cases:
            with self.subTest(pending=pending):
                milestones = (
                    tuple(
                        activity(name=f"Step {i + 1}", order=i + 1)
                        for i in range(pending)
                    )
                    + (value(),)
                )
                account = window_account(
                    D, elapsed=14, total=20, milestones=milestones
                )
                self.assertEqual(
                    priority_score(account, D).closeness.points, expected
                )

    def test_pending_value_milestone_does_not_count(self):
        milestones = (activity(status=MilestoneStatus.DONE), value())
        account = window_account(
            D, elapsed=14, total=20, milestones=milestones
        )
        self.assertEqual(priority_score(account, D).closeness.points, 20)


class TieBreakTests(unittest.TestCase):
    """Case 16: total desc, then urgency desc, then stagnation desc, then name."""

    def _blocked(self, name: str, *, target_offset: int, opened_days_ago: int,
                 pending_activities: int = 0, next_action=None):
        milestones = (
            tuple(
                activity(name=f"Step {i + 1}", order=i + 1)
                for i in range(pending_activities)
            )
            + (value(),)
        )
        return make_account(
            id=name.lower(),
            name=name,
            start=D - timedelta(days=14),
            target=D + timedelta(days=target_offset),
            owner="Ana",
            milestones=milestones,
            blockers=(blocker(opened_at=D - timedelta(days=opened_days_ago)),),
            next_action=next_action,
        )

    def test_equal_totals_higher_urgency_wins_over_name(self):
        # ZZZ: urgency 40 (days_left 1), stagnation 0, closeness 20, follow-up 0 = 60.
        # AAA: urgency 20 (consumption 0.78, days_left 4), stagnation 20, closeness 10, follow-up 10 = 60.
        zzz = self._blocked(
            "ZZZ Corp",
            target_offset=1,
            opened_days_ago=2,
            next_action=NextAction("Confirm data mapping", "Ana",
                                   D + timedelta(days=5)),
        )
        aaa = self._blocked("AAA Corp", target_offset=4, opened_days_ago=6,
                            pending_activities=1)
        self.assertEqual(priority_score(zzz, D).total, 60)
        self.assertEqual(priority_score(aaa, D).total, 60)

        plan = plan_week((aaa, zzz), D, slots=1)
        self.assertEqual(plan.intervention[0].account.name, "ZZZ Corp")

    def test_equal_total_and_urgency_higher_stagnation_wins(self):
        # AAA: urgency 40, stagnation 0, closeness 20, follow-up 10 = 70.
        # ZZZ: urgency 40, stagnation 10, closeness 10, follow-up 10 = 70.
        aaa = self._blocked("AAA Corp", target_offset=1, opened_days_ago=2)
        zzz = self._blocked("ZZZ Corp", target_offset=1, opened_days_ago=4,
                            pending_activities=1)
        self.assertEqual(priority_score(aaa, D).total, 70)
        self.assertEqual(priority_score(zzz, D).total, 70)

        plan = plan_week((aaa, zzz), D, slots=1)
        self.assertEqual(plan.intervention[0].account.name, "ZZZ Corp")

    def test_full_tie_falls_back_to_name(self):
        aaa = self._blocked("AAA Corp", target_offset=1, opened_days_ago=4)
        zzz = self._blocked("ZZZ Corp", target_offset=1, opened_days_ago=4)
        plan = plan_week((zzz, aaa), D, slots=1)
        self.assertEqual(plan.intervention[0].account.name, "AAA Corp")


class CapacityTests(unittest.TestCase):
    """Waiting-for-capacity entries explain why they ranked lower."""

    def test_capacity_entry_mentions_score_and_slots(self):
        high = self._blocked("High", target_offset=1, opened_days_ago=4)  # 80
        low = self._blocked("Low", target_offset=4, opened_days_ago=4)    # 60
        plan = plan_week((high, low), D, slots=1)
        self.assertEqual(
            [e.account.name for e in plan.intervention], ["High"]
        )
        waiting = plan.waiting_for_capacity
        self.assertEqual([e.account.name for e in waiting], ["Low"])
        self.assertIn("60", waiting[0].reason)
        self.assertIn("slot", waiting[0].reason)
        self.assertIn("Ranked #2", waiting[0].reason)

    def _blocked(self, name: str, *, target_offset: int, opened_days_ago: int):
        return make_account(
            id=name.lower(),
            name=name,
            start=D - timedelta(days=14),
            target=D + timedelta(days=target_offset),
            owner="Ana",
            milestones=(value(),),
            blockers=(blocker(opened_at=D - timedelta(days=opened_days_ago)),),
        )


if __name__ == "__main__":
    unittest.main()
