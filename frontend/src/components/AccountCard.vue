<script setup lang="ts">
import { computed } from "vue"
import { useRouter } from "vue-router"
import type { Account } from "@/types/workbench"
import {
  buildMilestones,
  statusClass,
  statusLabel,
  targetLabel,
} from "@/utils/workbench"

const props = defineProps<{
  account: Account
  today: string
}>()

const router = useRouter()

const milestones = computed(() => buildMilestones(props.account))
const milestoneProgress = computed(() => {
  const done = milestones.value.filter((m) => m.state === "done").length
  return { done, total: milestones.value.length }
})
const milestonePct = computed(() =>
  milestoneProgress.value.total
    ? Math.round((milestoneProgress.value.done / milestoneProgress.value.total) * 100)
    : 0,
)

function open(): void {
  router.push({ name: "account", params: { slug: props.account.slug } })
}
</script>

<template>
  <article
    class="account-card"
    :class="statusClass(account.status)"
    role="link"
    tabindex="0"
    @click="open"
    @keydown.enter="open"
  >
    <header class="account-card-header">
      <h3>{{ account.name }}</h3>
      <span class="status-badge" :class="statusClass(account.status)">
        <span class="badge-dot" aria-hidden="true"></span>
        {{ statusLabel(account.status) }}
      </span>
      <span class="account-target">{{ targetLabel(account.target_date, today) }}</span>
    </header>

    <dl class="account-facts">
      <div>
        <dt>Owner</dt>
        <dd>{{ account.owner ?? "No owner" }}</dd>
      </div>
      <div v-if="account.next_action">
        <dt>Next action</dt>
        <dd>{{ account.next_action }}</dd>
      </div>
    </dl>

    <div class="milestones-head">
      <span class="block-label">Milestones</span>
      <span class="milestone-count">{{ milestoneProgress.done }}/{{ milestoneProgress.total }}</span>
    </div>
    <div class="milestone-progress-track" aria-hidden="true">
      <div class="milestone-progress-fill" :style="{ width: `${milestonePct}%` }"></div>
    </div>

    <div v-if="account.internal_blocker" class="blocker-box">
      <span>Internal: {{ account.internal_blocker }}</span>
    </div>
    <div v-if="account.customer_blocker" class="blocker-box">
      <span>Customer: {{ account.customer_blocker }}</span>
    </div>

    <div class="account-foot">
      <span class="text-link">Open account →</span>
    </div>
  </article>
</template>
