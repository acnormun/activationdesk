export interface User {
  id: number
  username: string
  role: string
  account_ref: string | null
}

export interface Workspace {
  id: number
  name: string
}

/** Shape returned by POST /auth/login and GET /auth/me. */
export interface SessionResponse {
  user: User
  workspace: Workspace
}
