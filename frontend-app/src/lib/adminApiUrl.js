import { getApiBase } from './apiBase'

/**
 * Admin API path. In Vite dev, use relative `/api/admin` so requests go through the proxy.
 * For static builds, set `VITE_API_BASE` (no trailing slash) to your API origin.
 */
export function adminApiUrl(subpath) {
  const path = subpath.startsWith('/') ? subpath : `/${subpath}`
  const b = getApiBase()
  return b ? `${b}/api/admin${path}` : `/api/admin${path}`
}
