import { describe, expect, it } from "vitest"
import { loginErrorMessage, validateLoginInput } from "../src/utils/auth"

describe("validateLoginInput", () => {
  it("rejects a blank username", () => {
    expect(validateLoginInput("", "secret")).toBe("Username is required.")
  })

  it("rejects a whitespace-only username", () => {
    expect(validateLoginInput("   ", "secret")).toBe("Username is required.")
  })

  it("rejects a blank password", () => {
    expect(validateLoginInput("manager", "")).toBe("Password is required.")
  })

  it("accepts valid credentials", () => {
    expect(validateLoginInput("manager", "manager123")).toBeNull()
  })
})

describe("loginErrorMessage", () => {
  it("maps 401 to invalid credentials", () => {
    expect(loginErrorMessage(401)).toBe("Invalid username or password.")
  })

  it("maps 403 to a forbidden message", () => {
    expect(loginErrorMessage(403)).toBe("You are not allowed to sign in.")
  })

  it("maps unexpected statuses to a generic message", () => {
    expect(loginErrorMessage(500)).toBe(
      "Unable to sign in right now. Please try again.",
    )
  })

  it("handles a missing status (network error)", () => {
    expect(loginErrorMessage(undefined)).toBe(
      "Unable to sign in right now. Please try again.",
    )
  })
})
