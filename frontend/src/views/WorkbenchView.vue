<script setup lang="ts">
import { computed, onMounted, ref } from "vue"
import { useRouter } from "vue-router"
import { logout, session } from "@/auth/session"
import { useWorkbenchStore } from "@/stores/workbench"
import AccountCard from "@/components/AccountCard.vue"
import type { Account, PlanEntry } from "@/types/workbench"
import {
  emptyFilterMessage,
  filterAccounts,
  statusClass,
  statusLabel,
  statusTone,
  targetLabel,
} from "@/utils/workbench"

const router = useRouter()
const store = useWorkbenchStore()

const accounts = computed(() => store.accounts)
const plan = computed(() => store.plan)
const today = computed(() => store.plan?.today ?? new Date().toISOString().slice(0, 10))
const statusFilter = ref("")
const query = ref("")

const filtered = computed(() =>
  filterAccounts(accounts.value, statusFilter.value, query.value),
)
const emptyMessage = computed(() => emptyFilterMessage(statusFilter.value, query.value))

const accountBySlug = computed(() => store.accountBySlug)

/** Data-driven summary: every number is derived from the accounts and plan. */
const verified = computed(() => accounts.value.filter((a) => a.status === "activated"))

const medianTvfv = computed(() => {
  const days: number[] = []
  for (const account of verified.value) {
    if (account.evidence_approved_at && account.start_date) {
      days.push(
        Math.round(
          (Date.parse(account.evidence_approved_at) - Date.parse(account.start_date)) / 86400000,
        ),
      )
    }
  }
  if (days.length === 0) return null
  const sorted = [...days].sort((a, b) => a - b)
  const mid = Math.floor(sorted.length / 2)
  return sorted.length % 2 ? sorted[mid] : Math.round((sorted[mid - 1] + sorted[mid]) / 2)
})

const metrics = computed(() => {
  const total = accounts.value.length
  const unverified = total - verified.value.length
  const onTime = verified.value.filter(
    (a) => a.evidence_approved_at != null && a.evidence_approved_at <= a.target_date,
  ).length
  const missingNextAction = accounts.value.filter(
    (a) => a.status !== "activated" && !a.next_action,
  ).length
  const customerGates = accounts.value.filter(
    (a) => a.status === "waiting_on_customer",
  ).length
  return {
    total,
    verifiedCount: verified.value.length,
    verifiedNames: verified.value.map((a) => a.name).join(", "),
    onTime,
    medianTvfv: medianTvfv.value,
    tvfvN: verified.value.length,
    missingNextAction,
    unverified,
    customerGates,
  }
})

const focusEntries = computed<PlanEntry[]>(() => plan.value?.lanes.intervention ?? [])
const attentionEntries = computed<PlanEntry[]>(() => [
  ...(plan.value?.lanes.triage ?? []),
  ...(plan.value?.lanes.nudge ?? []),
])

const FILTERS = [
  { key: "", label: "All" },
  { key: "activated", label: "Verified" },
  { key: "blocked_internal", label: "Internal fix" },
  { key: "waiting_on_customer", label: "Customer gate" },
  { key: "overdue", label: "Overdue" },
  { key: "on_track", label: "On track" },
]

function daysToTarget(account: Account): number {
  return Math.round((Date.parse(account.target_date) - Date.parse(today.value)) / 86400000)
}

function targetTone(days: number, verifiedAccount: boolean): string {
  if (verifiedAccount) return days < 0 ? "danger" : "verified"
  if (days < 0) return "danger"
  if (days <= 3) return "amber"
  return "neutral"
}

function chipLabel(account: Account, days: number): string {
  const base = targetLabel(account.target_date, today.value)
  return days >= 0 && days <= 3 && account.status !== "activated" ? `${base} · soon` : base
}

function openAccount(slug: string): void {
  router.push({ name: "account", params: { slug } })
}

async function onLogout(): Promise<void> {
  await logout()
  await router.push({ name: "login" })
}

onMounted(() => store.loadBoard())
</script>

<template>
  <div class="app-shell">
    <header class="app-header">
      <div class="header-inner">
        <a class="brand" href="#" @click.prevent="router.push({ name: 'workbench' })">
          <span class="brand-mark" aria-hidden="true">✓</span>
          <span class="brand-text">
            <span class="brand-name">Activation Desk</span>
            <span class="brand-sub">Onboarding workbench</span>
          </span>
        </a>
        <div class="header-tools">
          <span class="demo-chip" title="Demo workspace, seeded on login">
            Demo · {{ session.user?.username ?? "manager" }}
          </span>
          <button type="button" class="btn btn-ghost btn-sm" @click="onLogout">Sign out</button>
        </div>
      </div>
    </header>

    <main class="page">
      <p v-if="store.error" class="board-error">{{ store.error }}</p>

      <section class="hero">
        <p class="eyebrow">Onboarding workbench · invoice approvals</p>
        <h1>Six accounts. Two unblocks this week.</h1>
        <p class="lead">
          The shared checklist says what we finished. This workbench shows whether the customer
          reached first value — and who owns what is still blocking it.
        </p>
        <div class="hero-meta">
          <span class="clock-chip">🕒 Demo clock: {{ today }}</span>
          <span>Signed in as {{ session.user?.username ?? "manager" }} (single user)</span>
          <span>Capacity: 2 active unblocks</span>
        </div>
      </section>

      <section class="metrics" aria-label="Cohort metrics">
        <div class="stat tone-verified">
          <p class="stat-label">Verified first value</p>
          <p class="stat-value">{{ metrics.verifiedCount }} / {{ metrics.total }}</p>
          <p class="stat-detail">
            {{ metrics.verifiedNames || "No verified approvals yet" }}
            <template v-if="metrics.verifiedCount">· {{ metrics.onTime }} on time</template>
          </p>
        </div>
        <div class="stat tone-neutral">
          <p class="stat-label">Median time to verified value</p>
          <p class="stat-value">{{ metrics.medianTvfv === null ? "—" : `${metrics.medianTvfv} days` }}</p>
          <p class="stat-detail">n={{ metrics.tvfvN }} · kickoff → approval date</p>
        </div>
        <div class="stat tone-amber">
          <p class="stat-label">No next action</p>
          <p class="stat-value">{{ metrics.missingNextAction }}</p>
          <p class="stat-detail">of {{ metrics.unverified }} unverified accounts</p>
        </div>
        <div class="stat tone-customer">
          <p class="stat-label">Customer-owned gates</p>
          <p class="stat-value">{{ metrics.customerGates }}</p>
          <p class="stat-detail">Cannot be closed by internal tasks</p>
        </div>
      </section>

      <section class="section" aria-labelledby="focus-title">
        <div class="section-head">
          <div>
            <h2 id="focus-title">This week's two unblocks</h2>
            <p>A slot is a commitment to drive one account to verified first value, not a watchlist.</p>
          </div>
          <span class="capacity-chip" :class="{ 'is-full': focusEntries.length >= 2 }">
            {{ focusEntries.length }}/2 committed
          </span>
        </div>

        <div v-if="focusEntries.length === 0" class="empty-state">
          <h3>No intervention slots filled</h3>
          <p>{{ plan?.message || "No account is eligible for an intervention slot yet." }}</p>
        </div>
        <div v-else class="focus-grid">
          <article
            v-for="(entry, index) in focusEntries"
            :key="entry.account_slug"
            class="focus-card"
            :class="`tone-${statusTone(accountBySlug[entry.account_slug]?.status ?? '')}`"
          >
            <div class="focus-head">
              <div class="focus-title-wrap">
                <span class="slot-token">Slot {{ index + 1 }}</span>
                <h3>
                  <button type="button" class="focus-title-btn" @click="openAccount(entry.account_slug)">
                    {{ entry.account_name }}
                  </button>
                </h3>
              </div>
              <span class="status-badge" :class="statusClass(accountBySlug[entry.account_slug]?.status ?? '')">
                <span class="badge-dot" aria-hidden="true"></span>
                {{ statusLabel(accountBySlug[entry.account_slug]?.status ?? "") }}
              </span>
            </div>

            <div class="focus-meta">
              <span
                class="target-chip"
                :class="`tone-${targetTone(daysToTarget(accountBySlug[entry.account_slug]), accountBySlug[entry.account_slug]?.status === 'activated')}`"
              >
                {{ chipLabel(accountBySlug[entry.account_slug], daysToTarget(accountBySlug[entry.account_slug])) }}
              </span>
              <span v-if="entry.score_total != null" class="score-pill">{{ entry.score_total }} pts</span>
            </div>

            <div class="focus-block" v-if="accountBySlug[entry.account_slug]">
              <p class="block-label">Gate</p>
              <template v-if="accountBySlug[entry.account_slug].internal_blocker">
                <p class="focus-gate">{{ accountBySlug[entry.account_slug].internal_blocker }}</p>
                <p class="owner-line">
                  <span class="side-dot side-internal" aria-hidden="true"></span>
                  Internal · {{ accountBySlug[entry.account_slug].owner ?? "unassigned" }}
                </p>
              </template>
              <template v-else-if="accountBySlug[entry.account_slug].customer_blocker">
                <p class="focus-gate">{{ accountBySlug[entry.account_slug].customer_blocker }}</p>
                <p class="owner-line">
                  <span class="side-dot side-customer" aria-hidden="true"></span>
                  Customer-owned
                </p>
              </template>
              <p v-else class="focus-gate">No open gate — the commitment continues until first value is verified.</p>
            </div>

            <p class="focus-rationale">{{ entry.reason }}</p>

            <div class="focus-foot">
              <button type="button" class="btn btn-primary btn-sm" @click="openAccount(entry.account_slug)">
                Open account
              </button>
            </div>
          </article>
        </div>
      </section>

      <section v-if="attentionEntries.length > 0" class="section" aria-labelledby="triage-title">
        <div class="section-head">
          <div>
            <h2 id="triage-title">Resolve before planning</h2>
            <p>These accounts are not ignored — their next step needs a decision before a slot is spent.</p>
          </div>
          <span class="capacity-chip">{{ attentionEntries.length }} to resolve</span>
        </div>
        <div class="triage-grid">
          <button
            v-for="entry in attentionEntries"
            :key="entry.account_slug"
            type="button"
            class="triage-card"
            @click="openAccount(entry.account_slug)"
          >
            <div class="triage-top">
              <strong>{{ entry.account_name }}</strong>
              <span class="status-badge" :class="statusClass(accountBySlug[entry.account_slug]?.status ?? '')">
                <span class="badge-dot" aria-hidden="true"></span>
                {{ statusLabel(accountBySlug[entry.account_slug]?.status ?? "") }}
              </span>
            </div>
            <p class="triage-reason">{{ entry.reason }}</p>
            <div class="triage-meta" v-if="accountBySlug[entry.account_slug]">
              <span
                class="target-chip"
                :class="`tone-${targetTone(daysToTarget(accountBySlug[entry.account_slug]), false)}`"
              >
                {{ chipLabel(accountBySlug[entry.account_slug], daysToTarget(accountBySlug[entry.account_slug])) }}
              </span>
              <span v-if="entry.nudge_level">nudge: {{ entry.nudge_level }}</span>
            </div>
          </button>
        </div>
      </section>

      <section class="section" aria-labelledby="queue-title">
        <div class="section-head">
          <div>
            <h2 id="queue-title">Account queue</h2>
            <p>Ordered by decision state. Open an account to see the evidence and record the next move.</p>
          </div>
        </div>

        <div class="queue-card">
          <div class="queue-toolbar">
            <div class="filter-row" role="group" aria-label="Filter accounts">
              <button
                v-for="item in FILTERS"
                :key="item.key"
                type="button"
                class="filter-chip"
                :class="{ 'is-active': statusFilter === item.key }"
                :aria-pressed="statusFilter === item.key"
                @click="statusFilter = item.key"
              >
                {{ item.label }}
                <span class="filter-count">
                  {{ item.key === "" ? accounts.length : accounts.filter((a) => a.status === item.key).length }}
                </span>
              </button>
            </div>
            <div class="search-wrap">
              <input
                v-model="query"
                type="search"
                placeholder="Search account or owner"
                aria-label="Search accounts"
              />
            </div>
          </div>

          <p v-if="store.loading" class="panel-status">Loading accounts…</p>
          <p v-else-if="filtered.length === 0" class="panel-status">{{ emptyMessage }}</p>
          <ul v-else class="account-list">
            <li v-for="account in filtered" :key="account.slug">
              <AccountCard :account="account" :today="today" />
            </li>
          </ul>
        </div>
      </section>

      <div class="two-col">
        <section class="section" aria-labelledby="policy-title">
          <div class="section-head">
            <div>
              <h2 id="policy-title">How the two are chosen</h2>
              <p>A rule-based policy, not a prediction. The reasoning stays visible.</p>
            </div>
          </div>
          <div class="panel">
            <ol class="policy-list">
              <li><strong>Verified accounts leave the queue.</strong> First value is proven by an approval record, not by completed tasks.</li>
              <li><strong>A customer-owned gate never takes a slot.</strong> It is nudged (remind, then escalate) — we can chase it, not close it.</li>
              <li><strong>No owner means triage.</strong> An unowned account cannot be actioned reliably, so it is surfaced before any slot is spent.</li>
              <li><strong>Order by policy score, then urgency.</strong> The top two fill capacity.</li>
              <li><strong>Clearing a gate is progress, not activation.</strong> Only a recorded approval of a representative invoice activates an account.</li>
            </ol>
            <table class="score-table">
              <caption>Policy score components (points)</caption>
              <thead>
                <tr>
                  <th scope="col">Factor</th>
                  <th scope="col">Points</th>
                </tr>
              </thead>
              <tbody>
                <tr><td>Urgency</td><td>Overdue 50 · Critical (80%+ or ≤1 day) 40 · Attention (50–80%) 20 · Comfortable 0</td></tr>
                <tr><td>Stagnation</td><td>Oldest open internal blocker: 0–2d 0 · 3–5d 10 · 6+d 20</td></tr>
                <tr><td>Closeness to value</td><td>Pending activity milestones: 0 → 20 · 1 → 10 · 2+ → 0</td></tr>
                <tr><td>Follow-up</td><td>10 when next action is missing or its follow-up has passed</td></tr>
              </tbody>
            </table>
            <p class="policy-foot">
              The score orders work; it does not forecast whether the customer will activate. Missing information is shown as a gap, never guessed into a fact.
            </p>
          </div>
        </section>

        <section class="section" aria-labelledby="records-title">
          <div class="section-head">
            <div>
              <h2 id="records-title">About this workbench</h2>
              <p>What the tool tracks, and what it deliberately does not.</p>
            </div>
          </div>
          <div class="panel">
            <p class="body-copy">
              Every account carries a desired outcome, a target, activity milestones, a value
              milestone with approval evidence, open blockers (internal or customer-owned) and a
              next action with owner and follow-up. Status, flags and priority are recalculated from
              these facts after every change — never stored as a stale label.
            </p>
            <p class="body-copy" style="margin-top: 10px">
              Out of scope: a real invoice engine, CRM/calendar integration, messaging, multi-user
              permissions, and implementing the customer-owned dependency. The customer update that
              closes a customer blocker is labelled <span class="badge simulated">Simulated</span>.
            </p>
          </div>
        </section>
      </div>
    </main>

    <footer class="app-footer">
      <div class="footer-inner">
        <span>Synthetic demo data · single simulated user · persisted per workspace</span>
        <span>Activation Desk · onboarding workbench</span>
      </div>
    </footer>
  </div>
</template>
