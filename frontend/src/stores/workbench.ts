import { defineStore } from "pinia"
import { fetchAccountDetail, fetchAccounts, fetchWeekPlan } from "@/api/client"
import type { Account, AccountDetail, WeekPlan } from "@/types/workbench"

/** Shared workbench state: accounts, the week plan and the selected account. */
export const useWorkbenchStore = defineStore("workbench", {
  state: () => ({
    accounts: [] as Account[],
    plan: null as WeekPlan | null,
    selectedSlug: "" as string,
    detail: null as AccountDetail | null,
    loading: false,
    error: "",
  }),

  getters: {
    accountBySlug(state): Record<string, Account> {
      return Object.fromEntries(state.accounts.map((account) => [account.slug, account]))
    },
    selectedAccount(state): Account | undefined {
      return state.accounts.find((account) => account.slug === state.selectedSlug)
    },
  },

  actions: {
    async loadBoard(): Promise<void> {
      this.loading = true
      this.error = ""
      try {
        const [accountRows, weekPlan] = await Promise.all([fetchAccounts(), fetchWeekPlan()])
        this.accounts = accountRows
        this.plan = weekPlan
      } catch (error) {
        this.error =
          error instanceof Error ? error.message : "Unable to load the workbench."
      } finally {
        this.loading = false
      }
    },

    async loadDetail(slug: string): Promise<void> {
      this.selectedSlug = slug
      this.detail = null
      if (!slug) return
      try {
        this.detail = await fetchAccountDetail(slug)
      } catch (error) {
        this.error = error instanceof Error ? error.message : "Unable to load the account."
      }
    },

    async refresh(): Promise<void> {
      await this.loadBoard()
      if (this.selectedSlug) await this.loadDetail(this.selectedSlug)
    },
  },
})
