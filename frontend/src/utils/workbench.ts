/** Pure helpers for the workbench: lane metadata, labels, filters and
 * permission checks. Framework-free so vitest can test them directly. */

import type { Account, PermissionRow } from "@/types/workbench"

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

/** Whether the role may perform the action, from the /permissions matrix. */
export function roleCan(rows: PermissionRow[], action: string, role: string): boolean {
  const row = rows.find((entry) => entry.action === action)
  if (!row) return false
  return Boolean((row as unknown as Record<string, boolean>)[role])
}