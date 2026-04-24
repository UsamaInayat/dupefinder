/**
 * FastAPI origin for axios / image URLs.
 * - Local dev: `http://localhost:8000` (or `VITE_API_BASE` if set).
 * - Production (Vercel): empty string → browser uses same origin; `vercel.json` rewrites
 *   `/api`, `/data`, `/ping`, `/health` to the URL in `BACKEND_PUBLIC_URL` (see repo file).
 * - Override anytime with `VITE_API_BASE` (no trailing slash).
 */
export function getApiOrigin() {
  const env = (import.meta.env.VITE_API_BASE || '').replace(/\/$/, '')
  if (env) return env
  if (import.meta.env.DEV) return 'http://localhost:8000'
  return ''
}
