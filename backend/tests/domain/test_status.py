"""Seed-case tests for the Pipeline 1 status rules (first match wins)."""

import unittest
from dataclasses import replace
from datetime import timedelta

from app.domain.models import (
    BlockerStatus,
    Flag,
    NudgeLevel,
    ResolvedVia,
    Role,
    Status,
)
from app.domain.priority import Lane, plan_week
from app.domain.seed import SAMPLE_DAY, account_by_id
from app.domain.status import derive_status
from app.domain.validation import validate_blocker_resolution


class SeedStatusTests(unittest.TestCase):
    """Status cases 1-5 and the flags for every seeded account."""

    def test_gamma_activated_with_valid_evidence(self):
        """Case 1: value done + evidence that passes -> ACTIVATED."""
        gamma = account_by_id("gamma")
        result = derive_status(gamma, SAMPLE_DAY)
        self.assertIs(result.status, Status.ACTIVATED)
        self.assertEqual(result.flags, ())

    def test_alpha_blocked_internal_and_beta_waiting_on_customer(self):
        """Case 2: open internal blocker vs open customer blocker."""
        alpha = account_by_id("alpha")
        beta = account_by_id("beta")
        self.assertIs(derive_status(alpha, SAMPLE_DAY).status, Status.BLOCKED_INTERNAL)
        self.assertIs(
            derive_status(beta, SAMPLE_DAY).status, Status.WAITING_ON_CUSTOMER
        )

    def test_passed_target_never_pulls_beta_out_of_waiting(self):
        """Case 3: at D+3 Beta is past the target but the customer blocker
        still wins; it only adds the PAST_TARGET flag and escalates the
        nudge."""
        beta = account_by_id("beta")
        later = SAMPLE_DAY + timedelta(days=3)

        result = derive_status(beta, later)
        self.assertIs(result.status, Status.WAITING_ON_CUSTOMER)
        self.assertTrue(result.has_flag(Flag.PAST_TARGET))

        plan_later = plan_week((beta,), later)
        self.assertIs(plan_later.nudge[0].nudge_level, NudgeLevel.ESCALATE)

        plan_today = plan_week((beta,), SAMPLE_DAY)
        self.assertIs(plan_today.nudge[0].nudge_level, NudgeLevel.REMIND)

    def test_epsilon_overdue_without_owner(self):
        """Case 4: no blockers, target passed -> OVERDUE with NO_OWNER,
        and the plan sends it to triage."""
        epsilon = account_by_id("epsilon")
        result = derive_status(epsilon, SAMPLE_DAY)
        self.assertIs(result.status, Status.OVERDUE)
        self.assertTrue(result.has_flag(Flag.NO_OWNER))
        self.assertTrue(result.has_flag(Flag.PAST_TARGET))

        plan = plan_week((epsilon,), SAMPLE_DAY)
        self.assertIs(plan.triage[0].lane, Lane.TRIAGE)

    def test_delta_on_track(self):
        """Case 5: no blockers, target in the future -> ON_TRACK."""
        delta = account_by_id("delta")
        result = derive_status(delta, SAMPLE_DAY)
        self.assertIs(result.status, Status.ON_TRACK)
        self.assertEqual(result.flags, ())

    def test_flags_matrix_at_sample_day(self):
        """Flags only for non-activated accounts, in a stable order."""
        expected = {
            "alpha": (Flag.NO_NEXT_ACTION,),
            "beta": (Flag.NO_NEXT_ACTION,),
            "gamma": (),
            "delta": (),
            "epsilon": (Flag.NO_OWNER, Flag.NO_NEXT_ACTION, Flag.PAST_TARGET),
            "zeta": (Flag.NO_NEXT_ACTION,),
        }
        for account_id, flags in expected.items():
            with self.subTest(account=account_id):
                result = derive_status(account_by_id(account_id), SAMPLE_DAY)
                self.assertEqual(result.flags, flags)


class ResolvingBlockerTests(unittest.TestCase):
    """Case 7: fixing a blocker unblocks the account, it does not activate it."""

    def test_resolving_alpha_blocker_gives_on_track_not_activated(self):
        alpha = account_by_id("alpha")
        blocker = alpha.blockers[0]
        errors = validate_blocker_resolution(
            blocker, ResolvedVia.INTERNAL_FIX, Role.ONBOARDING_MANAGER
        )
        self.assertEqual(errors, [])

        resolved = replace(
            blocker,
            status=BlockerStatus.RESOLVED,
            resolved_via=ResolvedVia.INTERNAL_FIX,
            resolved_at=SAMPLE_DAY,
        )
        alpha_unblocked = replace(alpha, blockers=(resolved,))

        result = derive_status(alpha_unblocked, SAMPLE_DAY)
        self.assertIs(result.status, Status.ON_TRACK)
        self.assertIsNot(result.status, Status.ACTIVATED)


if __name__ == "__main__":
    unittest.main()
