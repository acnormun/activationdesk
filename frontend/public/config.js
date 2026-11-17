// Runtime API base. The Docker image rewrites the URL below at container
// start from the API_BASE environment variable (default http://localhost:8000).
// Leave it as an empty string ("") to call the API on the same origin.
window.__API_BASE__ = "http://localhost:8000";
