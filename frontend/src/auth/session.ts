import { reactive } from "vue"
import type { SessionResponse, User, Workspace } from "@/types/auth"

const API_BASE: string = ""

/** App-wide session state, restored from the HttpOnly cookie when needed. */
export const session = reactive({
  user: null as User | null,
  workspace: null as Workspace | null,
})

/** POST /auth/login: the backend sets the HttpOnly session cookie. */
export async function login(username: string, password: string): Promise<void> {
  const response = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ username, password }),
  })
  if (!response.ok) {
    const error = new Error("Login request failed") as Error & { status: number }
    error.status = response.status
    throw error
  }
  const data = (await response.json()) as SessionResponse
  session.user = data.user
  session.workspace = data.workspace
}

/** GET /auth/me: restores the session from the cookie; any failure clears it. */
export async function fetchSession(): Promise<void> {
  try {
    const response = await fetch(`${API_BASE}/auth/me`, {
      credentials: "include",
    })
    if (!response.ok) {
      throw new Error("Session is not valid")
    }
    const data = (await response.json()) as SessionResponse
    session.user = data.user
    session.workspace = data.workspace
  } catch {
    session.user = null
    session.workspace = null
  }
}

/** POST /auth/logout: clears the cookie server-side and the local state. */
export async function logout(): Promise<void> {
  try {
    await fetch(`${API_BASE}/auth/logout`, {
      method: "POST",
      credentials: "include",
    })
  } finally {
    session.user = null
    session.workspace = null
  }
}
