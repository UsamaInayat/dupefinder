/**
 * API origin (no trailing slash). Leave unset in dev: requests use same origin + Vite proxy (`/api` → localhost:8000).
 * For production, set e.g. `VITE_API_BASE=https://dupefinder-api.up.railway.app` at build time.
 */
export function getApiBase() {
  return (import.meta.env.VITE_API_BASE || '').replace(/\/$/, '')
}

/**
 * @param {string} path e.g. `/api/search/stats` or `api/auth/login`
 */
export function apiUrl(path) {
  const p = path.startsWith('/') ? path : `/${path}`
  const b = getApiBase()
  return b ? `${b}${p}` : p
}

/**
 * Product / static files served by the API under `/data/...` (see backend `app.mount("/data", ...)`).
 * @param {string} relativePath e.g. `product_images/xyz.jpg` or `data/foo.jpg` (strips a leading `data/` to avoid /data/data/...)
 */
export function publicDataUrl(relativePath) {
  if (!relativePath) return ''
  let rel = String(relativePath).replace(/\\/g, '/').replace(/^\//, '')
  if (rel.toLowerCase().startsWith('data/')) {
    rel = rel.slice(5)
  }
  if (!rel) return ''
  return apiUrl(`/data/${rel}`)
}

/**
 * Is this a full `http(s)` URL that points at our own API (no image-proxy needed for same-origin /data) ?
 * Used to decide when to use `/api/products/image-proxy` for hotlinked retail images.
 */
export function isOurApiAbsoluteUrl(url) {
  if (!url || !/^https?:\/\//i.test(url)) return true
  const b = getApiBase()
  if (b) return url.startsWith(b)
  return /localhost:8000|127\.0\.0\.1:8000/.test(url)
}
