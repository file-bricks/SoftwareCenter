import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import path from 'node:path'

const __dir = path.dirname(fileURLToPath(import.meta.url))
const root = path.join(__dir, '..')

// ── Dateien vorhanden ──────────────────────────────────────────────────────────

test('library.js existiert', () => {
  readFileSync(path.join(root, 'library.js'), 'utf8')
})

test('app.js existiert', () => {
  readFileSync(path.join(root, 'app.js'), 'utf8')
})

test('app.css existiert', () => {
  readFileSync(path.join(root, 'app.css'), 'utf8')
})

test('sw.js existiert', () => {
  readFileSync(path.join(root, 'sw.js'), 'utf8')
})

test('manifest.webmanifest existiert', () => {
  readFileSync(path.join(root, 'manifest.webmanifest'), 'utf8')
})

test('icons/Icon-192.png existiert', () => {
  readFileSync(path.join(root, 'icons', 'Icon-192.png'))
})

test('icons/Icon-512.png existiert', () => {
  readFileSync(path.join(root, 'icons', 'Icon-512.png'))
})

// ── Manifest ───────────────────────────────────────────────────────────────────

test('manifest.webmanifest ist gültiges JSON', () => {
  const raw = readFileSync(path.join(root, 'manifest.webmanifest'), 'utf8')
  JSON.parse(raw)
})

test('manifest hat Pflichtfelder name, short_name, start_url, icons', () => {
  const m = JSON.parse(readFileSync(path.join(root, 'manifest.webmanifest'), 'utf8'))
  assert.ok(m.name, 'name fehlt')
  assert.ok(m.short_name, 'short_name fehlt')
  assert.ok(m.start_url, 'start_url fehlt')
  assert.ok(Array.isArray(m.icons) && m.icons.length === 4, 'icons: 4 Einträge erwartet')
})

test('manifest hat purpose:any auf Regular-Icons (Bug #4 Fix)', () => {
  const m = JSON.parse(readFileSync(path.join(root, 'manifest.webmanifest'), 'utf8'))
  const anyIcons = m.icons.filter(i => i.purpose === 'any')
  assert.ok(anyIcons.length >= 2, `purpose:any muss auf mind. 2 Icons gesetzt sein, gefunden: ${anyIcons.length}`)
})

test('manifest hat lang-Feld', () => {
  const m = JSON.parse(readFileSync(path.join(root, 'manifest.webmanifest'), 'utf8'))
  assert.ok(m.lang, 'lang-Feld fehlt im Manifest')
})

// ── Service Worker ─────────────────────────────────────────────────────────────

test('sw.js enthält install-Listener', () => {
  const sw = readFileSync(path.join(root, 'sw.js'), 'utf8')
  assert.ok(sw.includes('install'), 'sw.js muss install-Event behandeln')
})

test('sw.js enthält fetch-Listener', () => {
  const sw = readFileSync(path.join(root, 'sw.js'), 'utf8')
  assert.ok(sw.includes('fetch'), 'sw.js muss fetch-Events behandeln')
})

test('sw.js enthält ignoreSearch:true (Bug #2 Fix — Offline-Fail bei ?demo=1)', () => {
  const sw = readFileSync(path.join(root, 'sw.js'), 'utf8')
  assert.ok(sw.includes('ignoreSearch'), 'caches.match muss ignoreSearch:true verwenden')
})

test('sw.js OFFLINE_ASSETS enthält Icon-Pfade (Bug #4 Fix)', () => {
  const sw = readFileSync(path.join(root, 'sw.js'), 'utf8')
  assert.ok(sw.includes('Icon-192.png'), 'Icon-192.png muss in OFFLINE_ASSETS sein')
  assert.ok(sw.includes('Icon-512.png'), 'Icon-512.png muss in OFFLINE_ASSETS sein')
  assert.ok(sw.includes('Icon-maskable-192.png'), 'Icon-maskable-192.png muss in OFFLINE_ASSETS sein')
  assert.ok(sw.includes('Icon-maskable-512.png'), 'Icon-maskable-512.png muss in OFFLINE_ASSETS sein')
})

// ── app.js ─────────────────────────────────────────────────────────────────────

test('app.js importiert aus library.js', () => {
  const js = readFileSync(path.join(root, 'app.js'), 'utf8')
  assert.ok(js.includes('./library.js'), 'app.js muss aus ./library.js importieren')
})

test('saveProfile ist gegen localStorage-Fehler gesichert (Bug #1 Fix — Safari Private Mode)', () => {
  const js = readFileSync(path.join(root, 'app.js'), 'utf8')
  const fnStart = js.indexOf('function saveProfile(')
  assert.ok(fnStart !== -1, 'saveProfile muss existieren')
  const fnBody = js.slice(fnStart).split(/\n(?=function )/)[0]
  assert.ok(fnBody.includes('try'), 'saveProfile muss localStorage.setItem in try/catch wrappen')
  assert.ok(fnBody.includes('catch'), 'saveProfile braucht catch-Block')
})

// ── package.json ───────────────────────────────────────────────────────────────

test('package.json hat test-Script (Bug #3 Fix)', () => {
  const pkg = JSON.parse(readFileSync(path.join(root, 'package.json'), 'utf8'))
  assert.ok(pkg.scripts?.test, 'package.json braucht scripts.test')
  assert.ok(pkg.scripts.test.includes('library.test.mjs'), 'test-Script muss library.test.mjs einschließen')
  assert.ok(pkg.scripts.test.includes('pwa.test.mjs'), 'test-Script muss pwa.test.mjs einschließen')
})
