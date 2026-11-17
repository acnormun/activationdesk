/** HTTP client for the workbench: every call sends the session cookie. */

import type {
  Account,
  AccountDetail,
  WeekPlan,
} from "@/types/workbench"

const API_BASE: string = import.meta.env.VITE_API_BASE ?? "http://localhost:8000"

/** Error carrying the HTTP status and the human-readable API detail. */
export class ApiError extends Error {
  status: number
  detail: string

  constructor(status: number, detail: string) {
    super(detail)
    this.status = status
    this.detail = detail
  }
}

async function parseError(response: Response): Promise<ApiError> {
  let detail = `Request failed with status ${response.status}.`
  try {
    const body = await response.json()
    if (typeof body.detail === "string") {
      detail = body.detail
    } else if (body.detail?.message) {
      detail = body.detail.message
    }
  } catch {
    // keep the default message
  }
  return new ApiError(response.status, detail)
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(body ?? {}),
  })
  if (!response.ok) {
    throw await parseError(response)
  }
  return (await response.json()) as T
}

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, { credentials: "include" })
  if (!response.ok) {
    throw await parseError(response)
  }
  return (await response.json()) as T
}

export function fetchAccounts(): Promise<Account[]> {
  return getJson("/accounts")
}

export function fetchAccountDetail(slug: string): Promise<AccountDetail> {
  return getJson(`/accounts/${slug}`)
}

export function fetchWeekPlan(slots = 2): Promise<WeekPlan> {
  return getJson(`/plan/week?slots=${slots}`)
}

export function assignOwner(slug: string, owner: string): Promise<Account> {
  return postJson(`/accounts/${slug}/owner`, { owner })
}

export function setNextAction(
  slug: string,
  nextAction: string,
  followUpDate: string,
): Promise<Account> {
  return postJson(`/accounts/${slug}/next-action`, {
    next_action: nextAction,
    follow_up_date: followUpDate,
  })
}

export function recordProgress(slug: string, note: string): Promise<Account> {
  return postJson(`/accounts/${slug}/progress`, { note })
}

export function openInternalBlocker(
  slug: string,
  description: string,
  milestone?: string | null,
): Promise<Account> {
  return postJson(`/accounts/${slug}/internal-blocker`, { description, milestone })
}

export function openCustomerBlocker(
  slug: string,
  description: string,
  milestone?: string | null,
): Promise<Account> {
  return postJson(`/accounts/${slug}/customer-blocker`, { description, milestone })
}

export function closeInternalBlocker(
  slug: string,
  resolutionNote: string,
): Promise<Account> {
  return postJson(`/accounts/${slug}/internal-blocker/close`, {
    resolution_note: resolutionNote,
  })
}

export function closeCustomerBlocker(
  slug: string,
  customerUpdate: string,
): Promise<Account> {
  return postJson(`/accounts/${slug}/customer-blocker/close`, {
    customer_update: customerUpdate,
  })
}

export function recordValueEvidence(
  slug: string,
  payload: {
    approved_by: string
    invoice_ref: string
    via_agreed_workflow: boolean
    approved_at: string
    recorded_by: string
  },
): Promise<Account> {
  return postJson(`/accounts/${slug}/value-evidence`, payload)
}

/** Record that an activity milestone (setup, import or training) is done. */
export function markMilestoneDone(slug: string, name: string): Promise<Account> {
  return postJson(`/accounts/${slug}/milestones/${name}`, {})
}