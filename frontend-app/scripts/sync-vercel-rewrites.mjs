/**
 * Reads BACKEND_PUBLIC_URL and writes frontend-app/vercel.json so Vercel can
 * proxy /api, /data, /ping, /health to your FastAPI (same-origin in the browser).
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const root = path.resolve(__dirname, '..')
const urlFile = path.join(root, 'BACKEND_PUBLIC_URL')

const PLACEHOLDER = 'REPLACE-WITH-YOUR-FASTAPI-HOST'

function readBackendUrl() {
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

const backend = readBackendUrl()

if (!backend) {
  console.error(
    '[deploy] Missing backend URL. Add one https:// line to frontend-app/BACKEND_PUBLIC_URL (see comments in that file).',
  )
  process.exit(1)
}

if (backend.includes(PLACEHOLDER)) {
  console.error(
    `[deploy] BACKEND_PUBLIC_URL still contains the placeholder "${PLACEHOLDER}".`,
    'Set it to your real FastAPI public URL, commit, and push.',
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
