<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from "vue"
import { useRouter } from "vue-router"
import { logout, session } from "@/auth/session"
import {
  ApiError,
  fetchAccountDetail,
  fetchAccounts,
  fetchWeekPlan,
} from "@/api/client"
import AccountCard from "@/components/AccountCard.vue"
import WeekPlanPanel from "@/components/WeekPlanPanel.vue"
import type { Account, AccountDetail, WeekPlan } from "@/types/workbench"
import { STATUS_LABELS, emptyFilterMessage, filterAccounts } from "@/utils/workbench"

const router = useRouter()

const accounts = ref<Account[]>([])
const plan = ref<WeekPlan | null>(null)
const detail = ref<AccountDetail | null>(null)
const selectedSlug = ref("")
const statusFilter = ref("")
const query = ref("")
const loading = ref(true)
const errorMessage = ref("")

/** The plan day, falling back to today before the plan loads. */
const today = computed(() => plan.value?.today ?? new Date().toISOString().slice(0, 10))

const filtered = computed(() =>
  filterAccounts(accounts.value, statusFilter.value, query.value),
)
const emptyMessage = computed(() => emptyFilterMessage(statusFilter.value, query.value))

async function loadBoard(): Promise<void> {
  loading.value = true
  errorMessage.value = ""
  try {
    const [accountRows, weekPlan] = await Promise.all([fetchAccounts(), fetchWeekPlan()])
    accounts.value = accountRows
    plan.value = weekPlan
  } catch (error) {
    errorMessage.value =
      error instanceof ApiError ? error.detail : "Unable to load the workbench. Please try again."
  } finally {
    loading.value = false
  }
}

async function loadDetail(slug: string): Promise<void> {
  selectedSlug.value = slug
  detail.value = null
  if (!slug) return
  try {
    detail.value = await fetchAccountDetail(slug)
  } catch (error) {
    errorMessage.value =
      error instanceof ApiError ? error.detail : "Unable to load the account history."
  }
}

/** Center the account card of a plan entry: clear filters if it is hidden, then scroll to it. */
async function focusPlanAccount(slug: string): Promise<void> {
  await loadDetail(slug)
  if (!filtered.value.some((account) => account.slug === slug)) {
    statusFilter.value = ""
    query.value = ""
  }
  await nextTick()
  document.getElementById(`account-card-${slug}`)?.scrollIntoView({
    behavior: "smooth",
    block: "center",
  })
}

async function refresh(): Promise<void> {
  await loadBoard()
  if (selectedSlug.value) await loadDetail(selectedSlug.value)
}

async function onLogout(): Promise<void> {
  await logout()
  await router.push({ name: "login" })
}

onMounted(loadBoard)
</script>

<template>
  <main class="workbench">
    <header class="workbench-header">
      <h1>Activation Desk</h1>
      <div v-if="session.user" class="workbench-session">
        <span>{{ session.workspace?.name }}</span>
        <span>{{ session.user.username }}</span>
        <button type="button" @click="onLogout">Sign out</button>
      </div>
    </header>

    <p v-if="errorMessage" class="board-error">{{ errorMessage }}</p>

    <section class="workbench-body">
      <div class="workbench-columns">
        <WeekPlanPanel :plan="plan" @select="focusPlanAccount" />

        <section class="accounts">
          <header class="accounts-header">
            <h2>Accounts</h2>
            <div class="filter-bar">
              <select v-model="statusFilter" aria-label="Filter by status">
                <option value="">All statuses</option>
                <option v-for="(label, value) in STATUS_LABELS" :key="value" :value="value">
                  {{ label }}
                </option>
              </select>
              <input
                v-model="query"
                type="search"
                placeholder="Search name, slug or owner"
                aria-label="Search accounts"
              />
            </div>
          </header>

          <p v-if="loading" class="panel-status">Loading accounts…</p>
          <p v-else-if="filtered.length === 0" class="panel-status">{{ emptyMessage }}</p>
          <ul v-else class="account-list">
            <li :id="`account-card-${account.slug}`" v-for="account in filtered" :key="account.slug">
              <AccountCard
                :account="account"
                :today="today"
                :selected="account.slug === selectedSlug"
                @changed="refresh"
                @select="loadDetail"
              />
            </li>
          </ul>
        </section>
      </div>

      <section v-if="selectedSlug" class="account-detail">
        <header class="account-detail-header">
          <h2>History: {{ detail?.account.name ?? selectedSlug }}</h2>
          <button type="button" @click="loadDetail('')">Close</button>
        </header>
        <p v-if="!detail" class="panel-status">Loading history…</p>
        <template v-else>
          <p v-if="detail.history.length === 0" class="panel-status">No recorded changes yet.</p>
          <ol v-else class="history-list">
            <li v-for="entry in detail.history" :key="entry.id">
              <span class="history-date">{{ entry.created_at.slice(0, 10) }}</span>
              <span class="history-action">{{ entry.action }}</span>
              <span>{{ entry.detail }}</span>
            </li>
          </ol>
        </template>
      </section>
    </section>
  </main>
</template>
