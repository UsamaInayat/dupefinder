import { getApiBase } from './apiBase'

/**
 * Admin API paths. Uses `/api/admin/...` on the current host (Vite proxy in dev; static builds use
 * `VITE_API_BASE` so requests hit your Railway / API host).
 */
export function adminApiUrl(subpath) {
  const path = subpath.startsWith('/') ? subpath : `/${subpath}`
  const b = getApiBase()
  return b ? `${b}/api/admin${path}` : `/api/admin${path}`
}
