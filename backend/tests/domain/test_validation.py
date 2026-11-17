"""Validation rule tests (cases 9-12): each function returns [] or errors."""

import unittest
from dataclasses import replace
from datetime import timedelta

from app.domain.models import (
    BlockerSide,
    BlockerStatus,
    MilestoneKind,
    NextAction,
    ResolvedVia,
    Role,
)
from app.domain.seed import SAMPLE_DAY, account_by_id
from app.domain.validation import (
    validate_blocker_resolution,
    validate_dates,
    validate_evidence,
    validate_milestones,
    validate_next_action,
)
from .factories import activity, blocker, value

D = SAMPLE_DAY


class EvidenceValidationTests(unittest.TestCase):
    """Case 9: evidence must be complete, on the value milestone, through
    the agreed workflow and not in the future."""

    def setUp(self):
        self.gamma = account_by_id("gamma")
        self.milestone = self.gamma.value_milestone
        self.evidence = self.milestone.evidence

    def test_gamma_evidence_is_valid(self):
        self.assertEqual(
            validate_evidence(self.evidence, self.milestone, D), []
        )

    def test_blank_fields_are_rejected(self):
        cases = {
            "approved_by": ("approver", replace(self.evidence, approved_by="   ")),
            "invoice_ref": ("invoice reference", replace(self.evidence, invoice_ref="")),
        }
        for field, (keyword, bad) in cases.items():
            with self.subTest(field=field):
                errors = validate_evidence(bad, self.milestone, D)
                self.assertEqual(len(errors), 1)
                self.assertIn(keyword, errors[0].lower())

    def test_workflow_requirement_rejects_off_workflow_approval(self):
        bad = replace(self.evidence, via_agreed_workflow=False)
        errors = validate_evidence(bad, self.milestone, D)
        self.assertEqual(len(errors), 1)
        self.assertTrue(
            errors[0].startswith(
                "Approval did not go through the agreed workflow"
            )
        )

    def test_future_approval_date_is_rejected(self):
        bad = replace(self.evidence, approved_at=D + timedelta(days=1))
        errors = validate_evidence(bad, self.milestone, D)
        self.assertEqual(len(errors), 1)
        self.assertIn("in the future", errors[0])

    def test_evidence_on_activity_milestone_is_rejected(self):
        setup = self.gamma.milestones[0]
        self.assertIs(setup.kind, MilestoneKind.ACTIVITY)
        errors = validate_evidence(self.evidence, setup, D)
        self.assertEqual(len(errors), 1)
        self.assertIn("VALUE milestone", errors[0])

    def test_missing_evidence_is_rejected(self):
        errors = validate_evidence(None, self.milestone, D)
        self.assertEqual(len(errors), 1)
        self.assertIn("Evidence is missing", errors[0])


class NextActionValidationTests(unittest.TestCase):
    """Case 10: description, owner and a follow-up not in the past."""

    def test_valid_action_with_follow_up_today_passes(self):
        action = NextAction("Send sample data", "Ana", D)
        self.assertEqual(validate_next_action(action, D), [])

    def test_blank_owner_is_rejected(self):
        action = NextAction("Send sample data", "  ", D)
        errors = validate_next_action(action, D)
        self.assertEqual(len(errors), 1)
        self.assertIn("owner", errors[0].lower())

    def test_blank_description_is_rejected(self):
        action = NextAction("", "Ana", D)
        errors = validate_next_action(action, D)
        self.assertEqual(len(errors), 1)
        self.assertIn("description", errors[0].lower())

    def test_past_follow_up_is_rejected(self):
        action = NextAction("Send sample data", "Ana", D - timedelta(days=1))
        errors = validate_next_action(action, D)
        self.assertEqual(len(errors), 1)
        self.assertIn("in the past", errors[0])


class BlockerResolutionValidationTests(unittest.TestCase):
    """Case 11: only the owner side can resolve, through the right route."""

    def setUp(self):
        self.alpha = account_by_id("alpha")
        self.internal = self.alpha.blockers[0]
        self.beta = account_by_id("beta")
        self.customer = self.beta.blockers[0]
        self.assertIs(self.internal.side, BlockerSide.INTERNAL)
        self.assertIs(self.customer.side, BlockerSide.CUSTOMER)

    def test_customer_blocker_needs_simulated_customer_update(self):
        errors = validate_blocker_resolution(
            self.customer, ResolvedVia.INTERNAL_FIX, Role.ONBOARDING_MANAGER
        )
        self.assertEqual(len(errors), 1)
        self.assertIn(
            "Only a customer update can resolve a customer-owned blocker",
            errors[0],
        )

    def test_customer_blocker_happy_path(self):
        errors = validate_blocker_resolution(
            self.customer,
            ResolvedVia.CUSTOMER_UPDATE_SIMULATED,
            Role.ONBOARDING_MANAGER,
        )
        self.assertEqual(errors, [])

    def test_internal_blocker_needs_internal_fix(self):
        errors = validate_blocker_resolution(
            self.internal,
            ResolvedVia.CUSTOMER_UPDATE_SIMULATED,
            Role.ONBOARDING_MANAGER,
        )
        self.assertEqual(len(errors), 1)
        self.assertIn("internal fix", errors[0])

    def test_internal_blocker_happy_path(self):
        errors = validate_blocker_resolution(
            self.internal, ResolvedVia.INTERNAL_FIX, Role.ONBOARDING_MANAGER
        )
        self.assertEqual(errors, [])

    def test_resolved_blocker_cannot_be_resolved_again(self):
        resolved = replace(self.internal, status=BlockerStatus.RESOLVED)
        errors = validate_blocker_resolution(
            resolved, ResolvedVia.INTERNAL_FIX, Role.ONBOARDING_MANAGER
        )
        self.assertEqual(len(errors), 1)
        self.assertIn("not open", errors[0])


class DatesAndMilestonesValidationTests(unittest.TestCase):
    """Case 12: target after start; exactly one VALUE milestone."""

    def test_target_must_be_after_start(self):
        self.assertEqual(validate_dates(D - timedelta(days=14), D), [])
        self.assertEqual(len(validate_dates(D - timedelta(days=14), D - timedelta(days=14))), 1)
        self.assertEqual(len(validate_dates(D - timedelta(days=14), D - timedelta(days=20))), 1)

    def test_dates_without_start_are_accepted(self):
        self.assertEqual(validate_dates(None, D), [])

    def test_exactly_one_value_milestone_is_valid(self):
        self.assertEqual(validate_milestones((value(),)), [])
        self.assertEqual(
            validate_milestones((activity(), value())), []
        )

    def test_zero_value_milestones_is_rejected(self):
        errors = validate_milestones((activity(),))
        self.assertEqual(len(errors), 1)
        self.assertIn("found 0", errors[0])

    def test_two_value_milestones_are_rejected(self):
        errors = validate_milestones((value(), value()))
        self.assertEqual(len(errors), 1)
        self.assertIn("found 2", errors[0])


if __name__ == "__main__":
    unittest.main()
