import test, { describe } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync, existsSync } from 'node:fs'
import { execSync } from 'node:child_process'
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

// ──────────────────────────────────────────────────────────────
// iOS PWA-Härtung
// ──────────────────────────────────────────────────────────────

describe('index.html iOS-PWA-Meta', () => {
  const html = readFileSync(path.join(root, 'index.html'), 'utf8')

  test('viewport-Meta enthält viewport-fit=cover', () => {
    assert.match(html, /<meta[^>]*name="viewport"[^>]*viewport-fit=cover/)
  })

  test('viewport-Meta enthält width=device-width und initial-scale=1', () => {
    assert.match(html, /<meta[^>]*name="viewport"[^>]*width=device-width/)
    assert.match(html, /<meta[^>]*name="viewport"[^>]*initial-scale=1/)
  })

  test('apple-mobile-web-app-title ist gesetzt', () => {
    assert.match(html, /<meta[^>]*name="apple-mobile-web-app-title"[^>]*content="[^"]+"/)
  })

  test('apple-mobile-web-app-status-bar-style ist gesetzt', () => {
    assert.match(html, /<meta[^>]*name="apple-mobile-web-app-status-bar-style"[^>]*content="[^"]+"/)
  })

  test('apple-touch-icon hat sizes="180x180"', () => {
    assert.match(html, /<link[^>]*rel="apple-touch-icon"[^>]*sizes="180x180"/)
  })

  test('apple-touch-icon verweist auf apple-touch-icon-180.png', () => {
    assert.match(html, /<link[^>]*rel="apple-touch-icon"[^>]*href="[^"]*apple-touch-icon-180\.png"/)
  })

  test('KEIN apple-mobile-web-app-capable (deprecated seit iOS 11.3)', () => {
    assert.doesNotMatch(html, /apple-mobile-web-app-capable/, 'deprecated — darf nicht gesetzt sein')
  })

  test('keine doppelten viewport-Meta-Tags', () => {
    const matches = html.match(/<meta[^>]*name="viewport"/g) ?? []
    assert.equal(matches.length, 1, `Genau 1 viewport-Meta erwartet, gefunden: ${matches.length}`)
  })

  test('theme-color Meta-Tag ist gesetzt', () => {
    assert.match(html, /<meta[^>]*name="theme-color"[^>]*content="[^"]+"/)
  })
})

describe('apple-touch-icon-180.png — opaques RGB', () => {
  const iconPath = path.join(root, 'icons', 'apple-touch-icon-180.png')

  test('apple-touch-icon-180.png existiert', () => {
    assert.ok(existsSync(iconPath), 'icons/apple-touch-icon-180.png fehlt')
  })

  test('apple-touch-icon-180.png ist opakes RGB (keine Transparenz)', () => {
    const p = iconPath.replace(/\\/g, '/')
    const result = execSync(
      `python -c "from PIL import Image; img=Image.open('${p}'); d=list(img.getdata()); t=sum(1 for px in d if len(px)==4 and px[3]==0); print(t)"`,
      { encoding: 'utf8' }
    ).trim()
    assert.equal(result, '0', `apple-touch-icon-180.png hat transparente Pixel: ${result}`)
  })
})

describe('sw.js iOS-Härtung', () => {
  const sw = readFileSync(path.join(root, 'sw.js'), 'utf8')

  test('CACHE_NAME ist v2 oder höher (nach iOS-Härtung)', () => {
    assert.match(sw, /softwarecenter-companion-v[2-9]/, 'CACHE_NAME muss v2+ sein')
  })

  test('apple-touch-icon-180.png ist in OFFLINE_ASSETS gecacht', () => {
    assert.ok(sw.includes('apple-touch-icon-180.png'), 'apple-touch-icon-180.png fehlt in OFFLINE_ASSETS')
  })
})
