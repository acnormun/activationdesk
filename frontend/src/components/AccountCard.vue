<script setup lang="ts">
import { computed, ref } from "vue"
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
import { flagLabel, statusClass, statusLabel, targetLabel } from "@/utils/workbench"

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
  openForm.value = openForm.value === name ? "" : name
}

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
  <article class="account-card" :class="{ selected }">
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
      <h4>Actions</h4>
      <div class="action-row">
        <button
          type="button"
          class="action"
          @click="toggleForm('owner')"
        >
          Assign owner
        </button>
        <button
          type="button"
          class="action"
          @click="toggleForm('target-date')"
        >
          Set target date
        </button>
        <button
          type="button"
          class="action"
          @click="toggleForm('next-action')"
        >
          Set next action
        </button>
        <button
          type="button"
          class="action"
          @click="toggleForm('progress')"
        >
          Record progress
        </button>
        <button
          v-if="!account.internal_blocker"
          type="button"
          class="action"
          @click="toggleForm('internal-blocker')"
        >
          Open internal blocker
        </button>
        <button
          v-if="!account.evidence_approved_by"
          type="button"
          class="action"
          @click="toggleForm('value-evidence')"
        >
          Record value evidence
        </button>
      </div>

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