/** Shapes returned by the /accounts and /plan/week endpoints. */

export interface Account {
  id: number
  slug: string
  name: string
  desired_outcome: string
  owner: string | null
  last_reviewed_at: string | null
  start_date: string
  target_date: string
  status: string
  flags: string[]
  next_action: string | null
  follow_up_date: string | null
  internal_blocker: string | null
  customer_blocker: string | null
  evidence_approved_by: string | null
  evidence_invoice_ref: string | null
  evidence_workflow_confirmed: boolean
  evidence_approved_at: string | null
  evidence_recorded_by: string | null
}

export interface HistoryEntry {
  id: number
  actor_role: string
  action: string
  detail: string
  created_at: string
}

/** Shape returned by GET /accounts/{slug}. */
export interface AccountDetail {
  account: Account
  history: HistoryEntry[]
}

export interface ScoreComponent {
  label: string
  points: number
  reason: string
  calculated: boolean
}

export interface PlanEntry {
  account_slug: string
  account_name: string
  lane: string
  reason: string
  nudge_level?: string
  score_total?: number
  score?: Record<"urgency" | "stagnation" | "closeness" | "followup", ScoreComponent>
}

export interface WeekPlan {
  today: string
  slots: number
  empty_slots: number
  message: string
  lanes: Record<string, PlanEntry[]>
}