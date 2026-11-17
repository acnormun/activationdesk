<script setup lang="ts">
import type { WeekPlan } from "@/types/workbench"
import { LANE_DESCRIPTIONS, LANE_LABELS, LANE_ORDER, laneClass } from "@/utils/workbench"

defineProps<{ plan: WeekPlan | null }>()

defineEmits<{ (event: "select", slug: string): void }>()
</script>

<template>
  <section v-if="plan" class="week-plan">
    <header class="week-plan-header">
      <h2>This week</h2>
      <p class="week-plan-slots">
        {{ plan.slots - plan.empty_slots }}/{{ plan.slots }} intervention slots used
      </p>
      <p v-if="plan.message" class="week-plan-message">{{ plan.message }}</p>
    </header>

    <div v-for="lane in LANE_ORDER" :key="lane" class="lane" :class="laneClass(lane)">
      <h3>{{ LANE_LABELS[lane] }}</h3>
      <p class="lane-description">{{ LANE_DESCRIPTIONS[lane] }}</p>
      <ul v-if="plan.lanes[lane]?.length" class="lane-entries">
        <li v-for="entry in plan.lanes[lane]" :key="entry.account_slug">
          <button type="button" class="plan-entry" @click="$emit('select', entry.account_slug)">
            <span class="plan-entry-name">{{ entry.account_name }}</span>
            <span v-if="entry.nudge_level" class="badge nudge">{{ entry.nudge_level }}</span>
            <span v-if="entry.score_total != null" class="badge score">
              {{ entry.score_total }} pts
            </span>
            <span class="plan-entry-reason">{{ entry.reason }}</span>
          </button>
        </li>
      </ul>
      <p v-else class="lane-empty">No accounts in this lane.</p>
    </div>
  </section>
  <p v-else class="panel-status">Loading the week plan…</p>
</template>