import { createRouter, createWebHistory } from "vue-router"
import { fetchSession, session } from "@/auth/session"
import LoginView from "@/views/LoginView.vue"
import WorkbenchView from "@/views/WorkbenchView.vue"

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", name: "workbench", component: WorkbenchView },
    { path: "/login", name: "login", component: LoginView },
  ],
})

// Global guard: every route is protected by default; /login is the only
// exception. Restores the session from the HttpOnly cookie when needed.
router.beforeEach(async (to) => {
  if (to.name === "login") {
    return true
  }
  if (session.user === null) {
    await fetchSession()
  }
  if (session.user === null) {
    return { name: "login" }
  }
  return true
})

export default router
