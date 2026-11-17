/** Returns an error message, or null when the input is valid. */
export function validateLoginInput(username: string, password: string): string | null {
  if (!username.trim()) return "Username is required."
  if (!password) return "Password is required."
  return null
}

/** Maps a failed login HTTP status to a user-facing message. */
export function loginErrorMessage(status?: number): string {
  if (status === 401) return "Invalid username or password."
  if (status === 403) return "You are not allowed to sign in."
  return "Unable to sign in right now. Please try again."
}
