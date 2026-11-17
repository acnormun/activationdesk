<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue"
import { useRoute, useRouter } from "vue-router"
import { useWorkbenchStore } from "@/stores/workbench"
import {
  ApiError,
  assignOwner,
  closeCustomerBlocker,
  closeInternalBlocker,
  openCustomerBlocker,
  openInternalBlocker,
  recordProgress,
  recordValueEvidence,
  setNextAction,
} from "@/api/client"
import {
  buildMilestones,
  flagLabel,
  statusClass,
  statusLabel,
  targetLabel,
} from "@/utils/workbench"

const route = useRoute()
const router = useRouter()
const store = useWorkbenchStore()

const slug = computed(() => route.params.slug as string)
const account = computed(() => store.detail?.account)
const history = computed(() => store.detail?.history ?? [])
const today = computed(() => store.plan?.today ?? new Date().toISOString().slice(0, 10))

const canAct = computed(() => account.value?.status !== "activated")

// ---- form state ----
const errorMessage = ref("")
const working = ref(false)
const openForm = ref("")
const ownerInput = ref("")
const nextActionInput = ref("")
const followUpInput = ref(today.value)
const progressInput = ref("")
const blockerInput = ref("")
const blockerMilestoneInput = ref("")
const customerBlockerInput = ref("")
const customerBlockerMilestoneInput = ref("")
const customerUpdateInput = ref("")
const internalCloseNote = ref("")
const evidenceForm = ref({
  approved_by: "",
  invoice_ref: "",
  approved_at: today.value,
  recorded_by: "",
  via_agreed_workflow: true,
})

const milestones = computed(() => (account.value ? buildMilestones(account.value) : []))

function daysToTarget(): number {
  if (!account.value) return 0
  return Math.round((Date.parse(account.value.target_date) - Date.parse(today.value)) / 86400000)
}

function targetTone(days: number, verifiedAccount: boolean): string {
  if (verifiedAccount) return days < 0 ? "danger" : "verified"
  if (days < 0) return "danger"
  if (days <= 3) return "amber"
  return "neutral"
}

function toggleForm(name: string): void {
  errorMessage.value = ""
  openForm.value = openForm.value === name ? "" : name
}

async function run(action: () => Promise<unknown>): Promise<void> {
  errorMessage.value = ""
  working.value = true
  try {
    await action()
    openForm.value = ""
    await store.refresh()
  } catch (error) {
    errorMessage.value =
      error instanceof ApiError ? error.detail : "Something went wrong. Please try again."
  } finally {
    working.value = false
  }
}

onMounted(async () => {
  await store.loadDetail(slug.value)
})

watch(slug, async (value) => {
  await store.loadDetail(value)
})
</script>

<template>
  <main class="page detail-page">
    <a class="back-link" href="#" @click.prevent="router.push({ name: 'workbench' })">
      ← Workbench
    </a>

    <p v-if="store.error" class="board-error">{{ store.error }}</p>

    <div v-if="!account" class="panel-status">Loading account…</div>

    <template v-if="account">
      <header class="detail-head">
        <div class="detail-head-main">
          <div class="detail-title-row">
            <h1>{{ account.name }}</h1>
            <span class="status-badge" :class="statusClass(account.status)">
              <span class="badge-dot" aria-hidden="true"></span>
              {{ statusLabel(account.status) }}
            </span>
            <span v-for="flag in account.flags" :key="flag" class="flag-badge">
              {{ flagLabel(flag) }}
            </span>
          </div>
          <div class="detail-meta">
            <span class="target-chip" :class="`tone-${targetTone(daysToTarget(), account.status === 'activated')}`">
              {{ targetLabel(account.target_date, today) }}
            </span>
            <span>Target {{ account.target_date }}</span>
            <span>Started {{ account.start_date }}</span>
          </div>
        </div>
      </header>

      <section class="card">
        <div class="card-head">
          <h2>Outcome &amp; ownership</h2>
        </div>
        <div class="card-body">
          <p class="block-label">Desired outcome</p>
          <p class="outcome-copy">{{ account.desired_outcome }}</p>
          <p class="block-label">Owner</p>
          <p class="body-copy">{{ account.owner ?? "No owner" }}</p>
          <p class="block-label">Next action</p>
          <p class="body-copy">
            {{ account.next_action ? `${account.next_action} · follow-up ${account.follow_up_date ?? "unscheduled"}` : "None recorded" }}
          </p>
        </div>
      </section>

      <section class="card">
        <div class="card-head">
          <h2>Path to first value</h2>
          <span class="card-note">{{ milestones.filter((m) => m.state === "done").length }}/{{ milestones.length }} done</span>
        </div>
        <div class="card-body">
          <div class="milestone-progress-track" aria-hidden="true">
            <div
              class="milestone-progress-fill"
              :style="{ width: `${milestones.length ? Math.round((milestones.filter((m) => m.state === 'done').length / milestones.length) * 100) : 0}%` }"
            ></div>
          </div>
          <ol class="path-timeline">
            <li
              v-for="check in milestones"
              :key="check.label"
              class="path-item"
              :class="{ done: check.state === 'done', 'is-value': check.label === 'First value' }"
            >
              <span class="path-marker" aria-hidden="true">
                <svg v-if="check.state === 'done'" viewBox="0 0 20 20" class="path-check">
                  <path d="M4 10.5l4 4 8-9" />
                </svg>
                <span v-else class="path-dot"></span>
              </span>
              <div class="path-body">
                <span class="path-label">
                  {{ check.label }}
                  <span v-if="check.label === 'First value'" class="path-value-tag">key result</span>
                </span>
                <span class="path-detail">{{ check.detail }}</span>
              </div>
            </li>
          </ol>
        </div>
      </section>

      <section class="card">
        <div class="card-head">
          <h2>Blocking dependency</h2>
        </div>
        <div class="card-body">
          <div v-if="account.internal_blocker" class="blocker-box">
            <span>
              Internal blocker: {{ account.internal_blocker }}
              <em v-if="account.internal_blocker_milestone">· holds up {{ account.internal_blocker_milestone }}</em>
            </span>
            <button v-if="canAct" type="button" class="btn btn-secondary btn-sm" :disabled="working" @click="toggleForm('internal-blocker-close')">
              Close blocker
            </button>
          </div>
          <form v-if="openForm === 'internal-blocker-close'" class="account-action-form" @submit.prevent="run(() => closeInternalBlocker(account!.slug, internalCloseNote))">
            <label>What was fixed? (resolution note) <input v-model="internalCloseNote" type="text" required /></label>
            <button type="submit" class="btn btn-secondary btn-sm" :disabled="working">Close blocker</button>
          </form>

          <div v-if="account.customer_blocker" class="blocker-box">
            <span>
              Customer blocker: {{ account.customer_blocker }}
              <em v-if="account.customer_blocker_milestone">· holds up {{ account.customer_blocker_milestone }}</em>
            </span>
            <button v-if="canAct" type="button" class="btn btn-secondary btn-sm" :disabled="working" @click="toggleForm('customer-blocker')">
              Record customer update
            </button>
          </div>
          <form v-if="openForm === 'customer-blocker'" class="account-action-form" @submit.prevent="run(() => closeCustomerBlocker(account!.slug, customerUpdateInput))">
            <label>What did the customer provide? (simulated update) <input v-model="customerUpdateInput" type="text" required /></label>
            <button type="submit" class="btn btn-secondary btn-sm" :disabled="working">Close customer blocker</button>
          </form>

          <p v-if="!account.internal_blocker && !account.customer_blocker" class="body-copy">
            No open blocker recorded. That is not the same as "no blocker" — confirm the account state before assuming it is healthy.
          </p>
        </div>
      </section>

      <section v-if="account.evidence_approved_by" class="card">
        <div class="card-head">
          <h2>First value evidence</h2>
          <span class="badge tone-verified"><span class="badge-dot" aria-hidden="true"></span>Verified</span>
        </div>
        <div class="card-body">
          <p class="body-copy">
            Invoice {{ account.evidence_invoice_ref }} approved by {{ account.evidence_approved_by }} on
            {{ account.evidence_approved_at }} — via the agreed workflow.
          </p>
          <p class="card-caption">Recorded by {{ account.evidence_recorded_by }}.</p>
        </div>
      </section>

      <section v-if="canAct" class="card">
        <div class="card-head">
          <h2>Record a move</h2>
        </div>
        <div class="card-body">
          <div class="detail-actions">
            <button type="button" class="btn btn-secondary btn-sm" :class="{ 'is-active': openForm === 'owner' }" @click="toggleForm('owner')">Assign owner</button>
            <button type="button" class="btn btn-secondary btn-sm" :class="{ 'is-active': openForm === 'next-action' }" @click="toggleForm('next-action')">Set next action</button>
            <button type="button" class="btn btn-secondary btn-sm" :class="{ 'is-active': openForm === 'progress' }" @click="toggleForm('progress')">Record progress</button>
            <button v-if="!account.internal_blocker" type="button" class="btn btn-secondary btn-sm" :class="{ 'is-active': openForm === 'internal-blocker' }" @click="toggleForm('internal-blocker')">Open internal blocker</button>
            <button v-if="!account.customer_blocker" type="button" class="btn btn-secondary btn-sm" :class="{ 'is-active': openForm === 'customer-blocker-open' }" @click="toggleForm('customer-blocker-open')">Open customer blocker</button>
            <button v-if="!account.evidence_approved_by" type="button" class="btn btn-primary btn-sm" :class="{ 'is-active': openForm === 'value-evidence' }" @click="toggleForm('value-evidence')">Confirm first value</button>
          </div>

          <form v-if="openForm === 'owner'" class="account-action-form" @submit.prevent="run(() => assignOwner(account!.slug, ownerInput))">
            <label>Owner name <input v-model="ownerInput" type="text" required /></label>
            <button type="submit" class="btn btn-secondary btn-sm" :disabled="working">Save owner</button>
          </form>

          <form v-if="openForm === 'next-action'" class="account-action-form" @submit.prevent="run(() => setNextAction(account!.slug, nextActionInput, followUpInput))">
            <label>Next action <input v-model="nextActionInput" type="text" required /></label>
            <label>Follow-up date <input v-model="followUpInput" type="date" required /></label>
            <button type="submit" class="btn btn-secondary btn-sm" :disabled="working">Save next action</button>
          </form>

          <form v-if="openForm === 'progress'" class="account-action-form" @submit.prevent="run(() => recordProgress(account!.slug, progressInput))">
            <label>Progress note <input v-model="progressInput" type="text" required /></label>
            <button type="submit" class="btn btn-secondary btn-sm" :disabled="working">Save note</button>
          </form>

          <form v-if="openForm === 'internal-blocker'" class="account-action-form" @submit.prevent="run(() => openInternalBlocker(account!.slug, blockerInput, blockerMilestoneInput))">
            <label>What is blocking us internally? <input v-model="blockerInput" type="text" required /></label>
            <label>Which milestone is it holding up?
              <select v-model="blockerMilestoneInput" required>
                <option value="" disabled>Select a milestone</option>
                <option value="setup">Setup</option>
                <option value="import">Import</option>
                <option value="training">Training</option>
                <option value="first_value">First value</option>
              </select>
            </label>
            <button type="submit" class="btn btn-secondary btn-sm" :disabled="working">Open blocker</button>
          </form>

          <form v-if="openForm === 'customer-blocker-open'" class="account-action-form" @submit.prevent="run(() => openCustomerBlocker(account!.slug, customerBlockerInput, customerBlockerMilestoneInput))">
            <label>What is blocking on the customer side? <input v-model="customerBlockerInput" type="text" required /></label>
            <label>Which milestone is it holding up?
              <select v-model="customerBlockerMilestoneInput" required>
                <option value="" disabled>Select a milestone</option>
                <option value="setup">Setup</option>
                <option value="import">Import</option>
                <option value="training">Training</option>
                <option value="first_value">First value</option>
              </select>
            </label>
            <button type="submit" class="btn btn-secondary btn-sm" :disabled="working">Open customer blocker</button>
          </form>

          <form v-if="openForm === 'value-evidence'" class="account-action-form" @submit.prevent="run(() => recordValueEvidence(account!.slug, evidenceForm))">
            <p class="field-hint">First value needs proof: who approved, which invoice, when, and that it went through the agreed workflow.</p>
            <label>Approved by (customer finance owner) <input v-model="evidenceForm.approved_by" type="text" required /></label>
            <label>Invoice reference <input v-model="evidenceForm.invoice_ref" type="text" required /></label>
            <label>Approved at <input v-model="evidenceForm.approved_at" type="date" required /></label>
            <label>Recorded by <input v-model="evidenceForm.recorded_by" type="text" required /></label>
            <label class="checkbox"><input v-model="evidenceForm.via_agreed_workflow" type="checkbox" /> Approved through the agreed workflow</label>
            <button type="submit" class="btn btn-primary btn-sm" :disabled="working">Record evidence</button>
          </form>

          <p v-if="errorMessage" class="action-error">{{ errorMessage }}</p>
        </div>
      </section>

      <section class="card">
        <div class="card-head">
          <h2>Change log</h2>
          <span class="card-note">Survives reload</span>
        </div>
        <div class="card-body">
          <p v-if="history.length === 0" class="panel-status">No recorded changes yet.</p>
          <ol v-else class="history-list">
            <li v-for="entry in history" :key="entry.id">
              <span class="history-date">{{ entry.created_at.slice(0, 10) }}</span>
              <span class="history-action">{{ entry.action }}</span>
              <span v-if="entry.simulated" class="badge simulated">Simulated</span>
              <span class="history-detail">{{ entry.detail }}</span>
            </li>
          </ol>
        </div>
      </section>
    </template>
  </main>
</template>
