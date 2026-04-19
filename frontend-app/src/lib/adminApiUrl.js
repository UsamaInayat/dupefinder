/**
 * Admin API base path. In Vite dev, use relative `/api/admin` so requests go through the proxy.
 * For static builds against a remote API, set `VITE_API_BASE` (no trailing slash).
 */
export function adminApiUrl(subpath) {
  const trimmed = (import.meta.env.VITE_API_BASE || '').replace(/\/$/, '')
  const path = subpath.startsWith('/') ? subpath : `/${subpath}`
  return trimmed ? `${trimmed}/api/admin${path}` : `/api/admin${path}`
}
