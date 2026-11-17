<script setup lang="ts">
import { useRouter } from "vue-router"
import { logout, session } from "@/auth/session"

const router = useRouter()

async function onLogout(): Promise<void> {
  await logout()
  await router.push({ name: "login" })
}
</script>

<template>
  <main class="workbench">
    <header class="workbench-header">
      <h1>Activation Desk</h1>
      <div v-if="session.user" class="workbench-session">
        <span>{{ session.user.username }} ({{ session.user.role }})</span>
        <button type="button" @click="onLogout">Sign out</button>
      </div>
    </header>
    <section class="workbench-body">
      <p>Workspace: {{ session.workspace?.name ?? "—" }}</p>
      <p>Customer screens are the next step.</p>
    </section>
  </main>
</template>
