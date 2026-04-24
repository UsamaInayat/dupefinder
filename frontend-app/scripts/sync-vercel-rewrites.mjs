/**
 * Writes frontend-app/vercel.json so Vercel can proxy /api, /data, /ping, /health to FastAPI
 * (same-origin in the browser).
 *
 * **Railway / Docker:** set `VITE_API_BASE` at build time (see Dockerfile ARG). The script
 * uses that and does not require BACKEND_PUBLIC_URL.
 *
 * **Vercel (file-based):** add one https:// line to BACKEND_PUBLIC_URL, or set BACKEND_PUBLIC_URL
 * in the project’s environment.
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const root = path.resolve(__dirname, '..')
const urlFile = path.join(root, 'BACKEND_PUBLIC_URL')

const PLACEHOLDER = 'REPLACE-WITH-YOUR-FASTAPI-HOST'

function readBackendUrlFile() {
  if (!fs.existsSync(urlFile)) {
    return ''
  }
  const raw = fs.readFileSync(urlFile, 'utf8')
  const lines = raw.split(/\r?\n/)
  for (const line of lines) {
    const t = line.trim()
    if (!t || t.startsWith('#')) continue
    if (t.startsWith('http://') || t.startsWith('https://')) {
      return t.replace(/\/$/, '')
    }
  }
  return ''
}

/**
 * @param {string | undefined} raw
 * @returns {string} empty if unset or still the placeholder
 */
function backendFromString(raw) {
  if (raw == null || !String(raw).trim()) return ''
  let s = String(raw).trim().replace(/\/$/, '')
  if (s.includes(PLACEHOLDER)) return ''
  if (!/^https?:\/\//i.test(s)) {
    s = `https://${s}`
  }
  return s
}

// Railway/Docker: VITE_API_BASE is the primary source. Also accept BACKEND_PUBLIC_URL as an env
// (some hosts inject that name). File is last.
let backend =
  backendFromString(process.env.VITE_API_BASE) ||
  backendFromString(process.env.BACKEND_PUBLIC_URL) ||
  (() => {
    const f = readBackendUrlFile()
    if (!f || f.includes(PLACEHOLDER)) return ''
    return f
  })()

if (!backend) {
  console.error(
    '[deploy] No backend URL for rewrites. Do one of:\n' +
      '  • Railway/Docker: set build-time `VITE_API_BASE` to your FastAPI public URL (no trailing slash).\n' +
      '  • Vercel: add a single https:// line in frontend-app/BACKEND_PUBLIC_URL, or set env BACKEND_PUBLIC_URL.',
  )
  process.exit(1)
}

const vercel = {
  $schema: 'https://openapi.vercel.sh/vercel.json',
  rewrites: [
    { source: '/api/:path*', destination: `${backend}/api/:path*` },
    { source: '/data/:path*', destination: `${backend}/data/:path*` },
    { source: '/ping', destination: `${backend}/ping` },
    { source: '/health', destination: `${backend}/health` },
    { source: '/(.*)', destination: '/index.html' },
  ],
}

fs.writeFileSync(path.join(root, 'vercel.json'), JSON.stringify(vercel, null, 2) + '\n')
console.log('[deploy] Wrote vercel.json → proxy to', backend)
