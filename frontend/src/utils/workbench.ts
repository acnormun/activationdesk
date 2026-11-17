/** Pure helpers for the workbench: lane metadata, labels and filters.
 * Framework-free so vitest can test them directly. */

import type { Account } from "@/types/workbench"

/** Display order of the week-plan lanes. */
export const LANE_ORDER = [
  "intervention",
  "waiting_for_capacity",
  "nudge",
  "triage",
  "monitor",
  "no_intervention",
] as const

export const LANE_LABELS: Record<string, string> = {
  intervention: "Intervention",
  waiting_for_capacity: "Waiting for capacity",
  nudge: "Nudge the customer",
  triage: "Triage",
  monitor: "Monitor",
  no_intervention: "No intervention",
}

export const LANE_DESCRIPTIONS: Record<string, string> = {
  intervention: "Accounts this week's slots are spent on.",
  waiting_for_capacity: "Ranked, but out of slots this week.",
  nudge: "Customer-side action needed; the team nudges.",
  triage: "No reliable owner or next step; fix the basics first.",
  monitor: "On track; check again next week.",
  no_intervention: "Activated, or nothing useful to do.",
}

/** Lane value to CSS class (snake_case to kebab-case). */
export function laneClass(lane: string): string {
  return `lane-${lane.replace(/_/g, "-")}`
}

export const STATUS_LABELS: Record<string, string> = {
  activated: "Activated",
  waiting_on_customer: "Waiting on customer",
  blocked_internal: "Blocked (internal)",
  overdue: "Overdue",
  on_track: "On track",
}

export function statusLabel(status: string): string {
  return STATUS_LABELS[status] ?? status
}

export function statusClass(status: string): string {
  return `status-${status.replace(/_/g, "-")}`
}

/** Tone (colour family) for a status, matching the reference design system. */
export const STATUS_TONES: Record<string, string> = {
  activated: "verified",
  blocked_internal: "internal",
  waiting_on_customer: "customer",
  overdue: "danger",
  on_track: "calm",
}

export function statusTone(status: string): string {
  return STATUS_TONES[status] ?? "neutral"
}

export const FLAG_LABELS: Record<string, string> = {
  no_owner: "No owner",
  no_next_action: "No next action",
  follow_up_late: "Follow-up late",
  past_target: "Past target",
}

export function flagLabel(flag: string): string {
  return FLAG_LABELS[flag] ?? flag
}

/** Human description of the target date relative to the plan day. */
export function targetLabel(target: string, today: string): string {
  const day = 24 * 60 * 60 * 1000
  const days = Math.round((Date.parse(target) - Date.parse(today)) / day)
  if (days === 0) return "target today"
  if (days === 1) return "target tomorrow"
  if (days > 1) return `target in ${days} days`
  if (days === -1) return "target was yesterday"
  return `target was ${-days} days ago`
}

/** Verification state of one account milestone. */
export type MilestoneState = "done" | "pending"

/** Display names for the activity milestone names. */
export const MILESTONE_LABELS: Record<string, string> = {
  setup: "Setup",
  import: "Import",
  training: "Training",
}

/** Human label for one activity milestone name. */
export function milestoneLabel(name: string): string {
  return MILESTONE_LABELS[name] ?? name
}

export interface MilestoneCheck {
  label: string
  state: MilestoneState
  detail: string
}

/** Milestone checklist for one account: the activity milestones plus the
 * "First value" milestone. Blockers and the next action are facts of their
 * own, not milestones, so they stay out of this list. */
export function buildMilestones(account: Account): MilestoneCheck[] {
  const checks: MilestoneCheck[] = account.activity_milestones.map((milestone) => ({
    label: milestoneLabel(milestone.name),
    state: milestone.done ? "done" : "pending",
    detail: milestone.done ? `Done ${milestone.completed_at ?? ""}`.trim() : "Not done yet",
  }))
  checks.push({
    label: "First value",
    state: account.evidence_approved_by ? "done" : "pending",
    detail: account.evidence_approved_by
      ? `Invoice ${account.evidence_invoice_ref} approved by ${account.evidence_approved_by} on ${account.evidence_approved_at ?? "?"}`
      : "No representative invoice approved yet",
  })
  return checks
}

/** Filter accounts by status and free text across slug, name and owner. */
export function filterAccounts(
  accounts: Account[],
  status: string,
  query: string,
): Account[] {
  const needle = query.trim().toLowerCase()
  return accounts.filter((account) => {
    if (status && account.status !== status) return false
    if (!needle) return true
    const haystack = `${account.slug} ${account.name} ${account.owner ?? ""}`.toLowerCase()
    return haystack.includes(needle)
  })
}

/** Explicit message for an empty (filtered) account list. */
export function emptyFilterMessage(status: string, query: string): string {
  const text = query.trim()
  if (status && text) {
    return `No ${statusLabel(status).toLowerCase()} accounts match "${text}".`
  }
  if (status) return `No ${statusLabel(status).toLowerCase()} accounts right now.`
  if (text) return `No accounts match "${text}".`
  return "No accounts in this workspace yet."
}