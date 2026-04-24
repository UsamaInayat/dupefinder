/**
 * Admin API paths. Uses `/api/admin/...` on the current host (Vite proxy in dev, Vercel rewrites in prod).
 * Optional: set `VITE_API_BASE` to call the API host directly instead.
 */
export function adminApiUrl(subpath) {
  const trimmed = (import.meta.env.VITE_API_BASE || '').replace(/\/$/, '')
  const path = subpath.startsWith('/') ? subpath : `/${subpath}`
  return trimmed ? `${trimmed}/api/admin${path}` : `/api/admin${path}`
}
