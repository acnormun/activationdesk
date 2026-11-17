/// <reference types="vite/client" />

export {}

declare global {
  interface Window {
    /** Runtime API base URL, set by /config.js before the app bundle loads. */
    __API_BASE__?: string
  }
}
