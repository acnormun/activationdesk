<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue"
import {
  ApiError,
  assignOwner,
  closeCustomerBlocker,
  closeInternalBlocker,
  openInternalBlocker,
  recordProgress,
  recordValueEvidence,
  setNextAction,
  setTargetDate,
} from "@/api/client"
import type { Account } from "@/types/workbench"
import {
  buildMilestones,
  flagLabel,
  statusClass,
  statusLabel,
  targetLabel,
} from "@/utils/workbench"

const props = defineProps<{
  account: Account
  today: string
  selected: boolean
}>()

const emit = defineEmits<{
  (event: "changed"): void
  (event: "select", slug: string): void
}>()

const openForm = ref("")
const errorMessage = ref("")
const working = ref(false)
const menuOpen = ref(false)
const cardRoot = ref<HTMLElement | null>(null)

const milestones = computed(() => buildMilestones(props.account))

const menuActions = computed(() => {
  const actions = [
    { name: "owner", label: "Assign owner" },
    { name: "target-date", label: "Set target date" },
    { name: "next-action", label: "Set next action" },
    { name: "progress", label: "Record progress" },
  ]
  if (!props.account.internal_blocker) {
    actions.push({ name: "internal-blocker", label: "Open internal blocker" })
  }
  if (!props.account.evidence_approved_by) {
    actions.push({ name: "value-evidence", label: "Record value evidence" })
  }
  return actions
})

const ownerInput = ref(props.account.owner ?? "")
const targetDateInput = ref(props.account.target_date)
const nextActionInput = ref("")
const followUpInput = ref(props.today)
const progressInput = ref("")
const blockerInput = ref("")
const customerUpdateInput = ref("")
const evidenceForm = ref({
  approved_by: "",
  invoice_ref: "",
  approved_at: props.today,
  recorded_by: "",
  via_agreed_workflow: true,
})

/** Activated accounts accept no further changes (the backend rejects them too). */
const canAct = computed(() => props.account.status !== "activated")

function toggleForm(name: string): void {
  errorMessage.value = ""
  menuOpen.value = false
  openForm.value = openForm.value === name ? "" : name
}

function toggleMenu(): void {
  menuOpen.value = !menuOpen.value
}

/** Close the actions menu when clicking anywhere outside the card. */
function onDocumentClick(event: MouseEvent): void {
  if (menuOpen.value && cardRoot.value && !cardRoot.value.contains(event.target as Node)) {
    menuOpen.value = false
  }
}

onMounted(() => document.addEventListener("click", onDocumentClick))
onBeforeUnmount(() => document.removeEventListener("click", onDocumentClick))

async function run(action: () => Promise<unknown>): Promise<void> {
  errorMessage.value = ""
  working.value = true
  try {
    await action()
    openForm.value = ""
    emit("changed")
  } catch (error) {
    errorMessage.value =
      error instanceof ApiError ? error.detail : "Something went wrong. Please try again."
  } finally {
    working.value = false
  }
}
</script>

<template>
  <article ref="cardRoot" class="account-card" :class="{ selected }">
    <header class="account-card-header" @click="$emit('select', account.slug)">
      <h3>{{ account.name }}</h3>
      <span class="account-slug">{{ account.slug }}</span>
      <span class="status-badge" :class="statusClass(account.status)">
        {{ statusLabel(account.status) }}
      </span>
      <span class="account-target">{{ targetLabel(account.target_date, today) }}</span>
      <span v-for="flag in account.flags" :key="flag" class="flag-badge">
        {{ flagLabel(flag) }}
      </span>
      <div v-if="canAct" class="card-menu" @click.stop>
        <button
          type="button"
          class="card-menu-trigger"
          aria-label="Open actions menu"
          :aria-expanded="menuOpen"
          @click.stop="toggleMenu"
        >
          ⋮
        </button>
        <div v-if="menuOpen" class="card-menu-dropdown">
          <button
            v-for="item in menuActions"
            :key="item.name"
            type="button"
            class="card-menu-item"
            @click="toggleForm(item.name)"
          >
            {{ item.label }}
          </button>
        </div>
      </div>
    </header>

    <dl class="account-facts">
      <div>
        <dt>Desired outcome</dt>
        <dd>{{ account.desired_outcome }}</dd>
      </div>
      <div>
        <dt>Owner</dt>
        <dd>{{ account.owner ?? "No owner" }}</dd>
      </div>
      <div>
        <dt>Next action</dt>
        <dd>
          <span v-if="account.next_action">
            {{ account.next_action }} (follow-up {{ account.follow_up_date ?? "unscheduled" }})
          </span>
          <span v-else>None recorded</span>
        </dd>
      </div>
    </dl>

    <section class="milestones" aria-label="Milestones">
      <h4>Milestones</h4>
      <ul>
        <li v-for="check in milestones" :key="check.label">
          <span class="milestone-badge" :class="`milestone-${check.state}`">
            {{ check.state }}
          </span>
          <span class="milestone-text">
            <span class="milestone-label">{{ check.label }}</span>
            <span class="milestone-detail">{{ check.detail }}</span>
          </span>
        </li>
      </ul>
    </section>

    <div v-if="account.evidence_approved_by" class="evidence-box">
      First value recorded: invoice {{ account.evidence_invoice_ref }} approved by
      {{ account.evidence_approved_by }} on {{ account.evidence_approved_at }} (recorded by
      {{ account.evidence_recorded_by }}).
    </div>
    <div v-else class="evidence-box pending">First value not recorded yet.</div>

    <div v-if="account.internal_blocker" class="blocker-box">
      <span>Internal blocker: {{ account.internal_blocker }}</span>
      <button
        v-if="canAct"
        type="button"
        :disabled="working"
        @click="run(() => closeInternalBlocker(account.slug))"
      >
        Close blocker
      </button>
    </div>
    <div v-if="account.customer_blocker" class="blocker-box">
      <span>Customer blocker: {{ account.customer_blocker }}</span>
      <button
        v-if="canAct"
        type="button"
        :disabled="working"
        @click="toggleForm('customer-blocker')"
      >
        Record customer update
      </button>
    </div>
    <form
      v-if="openForm === 'customer-blocker'"
      class="account-action-form"
      @submit.prevent="run(() => closeCustomerBlocker(account.slug, customerUpdateInput))"
    >
      <label>
        Simulated customer update (required)
        <input v-model="customerUpdateInput" type="text" required />
      </label>
      <button type="submit" :disabled="working">Close customer blocker</button>
    </form>

    <section v-if="canAct" class="account-actions">
      <form
        v-if="openForm === 'owner'"
        class="account-action-form"
        @submit.prevent="run(() => assignOwner(account.slug, ownerInput))"
      >
        <label>
          Owner name
          <input v-model="ownerInput" type="text" required />
        </label>
        <button type="submit" :disabled="working">Save owner</button>
      </form>

      <form
        v-if="openForm === 'target-date'"
        class="account-action-form"
        @submit.prevent="run(() => setTargetDate(account.slug, targetDateInput))"
      >
        <label>
          Target date
          <input v-model="targetDateInput" type="date" required />
        </label>
        <button type="submit" :disabled="working">Save target date</button>
      </form>

      <form
        v-if="openForm === 'next-action'"
        class="account-action-form"
        @submit.prevent="run(() => setNextAction(account.slug, nextActionInput, followUpInput))"
      >
        <label>
          Next action
          <input v-model="nextActionInput" type="text" required />
        </label>
        <label>
          Follow-up date
          <input v-model="followUpInput" type="date" required />
        </label>
        <button type="submit" :disabled="working">Save next action</button>
      </form>

      <form
        v-if="openForm === 'progress'"
        class="account-action-form"
        @submit.prevent="run(() => recordProgress(account.slug, progressInput))"
      >
        <label>
          Progress note
          <input v-model="progressInput" type="text" required />
        </label>
        <button type="submit" :disabled="working">Save note</button>
      </form>

      <form
        v-if="openForm === 'internal-blocker'"
        class="account-action-form"
        @submit.prevent="run(() => openInternalBlocker(account.slug, blockerInput))"
      >
        <label>
          What is blocking us internally?
          <input v-model="blockerInput" type="text" required />
        </label>
        <button type="submit" :disabled="working">Open blocker</button>
      </form>

      <form
        v-if="openForm === 'value-evidence'"
        class="account-action-form"
        @submit.prevent="run(() => recordValueEvidence(account.slug, evidenceForm))"
      >
        <label>
          Approved by (customer finance owner)
          <input v-model="evidenceForm.approved_by" type="text" required />
        </label>
        <label>
          Invoice reference
          <input v-model="evidenceForm.invoice_ref" type="text" required />
        </label>
        <label>
          Approved at
          <input v-model="evidenceForm.approved_at" type="date" required />
        </label>
        <label>
          Recorded by
          <input v-model="evidenceForm.recorded_by" type="text" required />
        </label>
        <label class="checkbox">
          <input v-model="evidenceForm.via_agreed_workflow" type="checkbox" />
          Approved through the agreed workflow
        </label>
        <button type="submit" :disabled="working">Record evidence</button>
      </form>
    </section>
    <p v-else class="activated-note">Activated: no further intervention is allowed.</p>

    <p v-if="errorMessage" class="action-error">{{ errorMessage }}</p>
  </article>
</template>