<script setup lang="ts">
import { onMounted, ref } from "vue"
import { useRouter } from "vue-router"
import { fetchSession, login, session } from "@/auth/session"
import { loginErrorMessage, validateLoginInput } from "@/utils/auth"

const router = useRouter()

const username = ref("")
const password = ref("")
const errorMessage = ref("")
const submitting = ref(false)

onMounted(async () => {
  if (session.user === null) {
    await fetchSession()
  }
  if (session.user) {
    await router.push({ name: "workbench" })
  }
})

async function onSubmit(): Promise<void> {
  errorMessage.value = ""
  const validationError = validateLoginInput(username.value, password.value)
  if (validationError) {
    errorMessage.value = validationError
    return
  }

  submitting.value = true
  try {
    await login(username.value.trim(), password.value)
    await router.push({ name: "workbench" })
  } catch (error) {
    const status = (error as Error & { status?: number }).status
    errorMessage.value = loginErrorMessage(status)
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <main class="login-page">
    <section class="login-card">
      <h1>Activation Desk</h1>
      <p class="login-subtitle">Sign in to your workbench</p>
      <form @submit.prevent="onSubmit">
        <label>
          Username
          <input
            v-model="username"
            name="username"
            autocomplete="username"
            autofocus
          />
        </label>
        <label>
          Password
          <input
            v-model="password"
            name="password"
            type="password"
            autocomplete="current-password"
          />
        </label>
        <p v-if="errorMessage" class="login-error" role="alert">
          {{ errorMessage }}
        </p>
        <button type="submit" :disabled="submitting">
          {{ submitting ? "Signing in…" : "Sign in" }}
        </button>
      </form>
      <p class="login-demo">Demo account: manager / manager123</p>
    </section>
  </main>
</template>
