import { describe, expect, it } from "vitest"
import {
  LANE_ORDER,
  buildMilestones,
  emptyFilterMessage,
  filterAccounts,
  flagLabel,
  laneClass,
  statusClass,
  statusLabel,
  targetLabel,
} from "../src/utils/workbench"
import type { Account } from "../src/types/workbench"

function account(overrides: Partial<Account> = {}): Account {
  return {
    id: 1,
    slug: "alpha",
    name: "Alpha Corp",
    desired_outcome: "outcome",
    owner: "Ana",
    last_reviewed_at: null,
    start_date: "2026-11-02",
    target_date: "2026-11-20",
    status: "blocked_internal",
    flags: [],
    next_action: null,
    follow_up_date: null,
    internal_blocker: null,
    customer_blocker: null,
    evidence_approved_by: null,
    evidence_invoice_ref: null,
    evidence_workflow_confirmed: false,
    evidence_approved_at: null,
    evidence_recorded_by: null,
    ...overrides,
  }
}

describe("lane metadata", () => {
  it("orders the six domain lanes", () => {
    expect(LANE_ORDER).toEqual([
      "intervention",
      "waiting_for_capacity",
      "nudge",
      "triage",
      "monitor",
      "no_intervention",
    ])
  })

  it("maps a lane to a CSS class", () => {
    expect(laneClass("no_intervention")).toBe("lane-no-intervention")
  })
})

describe("status and flag labels", () => {
  it("maps known statuses to human labels", () => {
    expect(statusLabel("waiting_on_customer")).toBe("Waiting on customer")
    expect(statusLabel("activated")).toBe("Activated")
  })

  it("falls back to the raw value for unknown statuses", () => {
    expect(statusLabel("mystery")).toBe("mystery")
  })

  it("maps statuses and flags to CSS classes and labels", () => {
    expect(statusClass("blocked_internal")).toBe("status-blocked-internal")
    expect(flagLabel("no_owner")).toBe("No owner")
    expect(flagLabel("custom")).toBe("custom")
  })
})

describe("targetLabel", () => {
  it("describes today, tomorrow and future targets", () => {
    expect(targetLabel("2026-11-17", "2026-11-17")).toBe("target today")
    expect(targetLabel("2026-11-18", "2026-11-17")).toBe("target tomorrow")
    expect(targetLabel("2026-11-20", "2026-11-17")).toBe("target in 3 days")
  })

  it("describes missed targets", () => {
    expect(targetLabel("2026-11-16", "2026-11-17")).toBe("target was yesterday")
    expect(targetLabel("2026-11-12", "2026-11-17")).toBe("target was 5 days ago")
  })
})

describe("filterAccounts", () => {
  const accounts = [
    account({ slug: "alpha", name: "Alpha Corp", owner: "Ana", status: "blocked_internal" }),
    account({ slug: "gamma", name: "Gamma SA", owner: "Ana", status: "activated" }),
    account({ slug: "zeta", name: "Zeta Inc", owner: null, status: "blocked_internal" }),
  ]

  it("keeps everything with no filters", () => {
    expect(filterAccounts(accounts, "", "")).toHaveLength(3)
  })

  it("filters by status", () => {
    expect(filterAccounts(accounts, "blocked_internal", "").map((a) => a.slug)).toEqual([
      "alpha",
      "zeta",
    ])
  })

  it("filters by free text across slug, name and owner", () => {
    expect(filterAccounts(accounts, "", "gamma").map((a) => a.slug)).toEqual(["gamma"])
    expect(filterAccounts(accounts, "", "ana").map((a) => a.slug)).toEqual([
      "alpha",
      "gamma",
    ])
  })

  it("combines both filters", () => {
    expect(filterAccounts(accounts, "activated", "alpha")).toEqual([])
  })
})

describe("emptyFilterMessage", () => {
  it("explains what to change", () => {
    expect(emptyFilterMessage("", "")).toBe("No accounts in this workspace yet.")
    expect(emptyFilterMessage("overdue", "")).toBe("No overdue accounts right now.")
    expect(emptyFilterMessage("", "nebula")).toBe('No accounts match "nebula".')
    expect(emptyFilterMessage("activated", "nebula")).toBe(
      'No activated accounts match "nebula".',
    )
  })
})

describe("buildMilestones", () => {
  it("marks all milestones pending on a fresh account", () => {
    const checks = buildMilestones(account())
    expect(checks.map((c) => [c.label, c.state])).toEqual([
      ["First value evidence", "pending"],
      ["Next action", "pending"],
      ["Internal blocker", "done"],
      ["Customer blocker", "done"],
    ])
  })

  it("marks recorded evidence and next action as done with details", () => {
    const checks = buildMilestones(
      account({
        next_action: "Send invoice sample",
        follow_up_date: "2026-11-20",
        evidence_approved_by: "Dana",
        evidence_invoice_ref: "INV-42",
        evidence_approved_at: "2026-11-15",
        evidence_recorded_by: "manager",
      }),
    )
    const [evidence, nextAction] = checks
    expect(evidence.state).toBe("done")
    expect(evidence.detail).toContain("INV-42")
    expect(evidence.detail).toContain("Dana")
    expect(nextAction.state).toBe("done")
    expect(nextAction.detail).toContain("Send invoice sample")
    expect(nextAction.detail).toContain("2026-11-20")
  })

  it("marks open blockers as blocked", () => {
    const checks = buildMilestones(
      account({ internal_blocker: "Waiting on security review", customer_blocker: "Needs legal" }),
    )
    expect(checks[2]).toMatchObject({ label: "Internal blocker", state: "blocked" })
    expect(checks[3]).toMatchObject({ label: "Customer blocker", state: "blocked" })
  })
})