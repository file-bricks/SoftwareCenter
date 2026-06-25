import test, { describe } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync, existsSync } from 'node:fs'
import { execFileSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'
import path from 'node:path'

const __dir = path.dirname(fileURLToPath(import.meta.url))
const root = path.join(__dir, '..')

const manifest = JSON.parse(readFileSync(path.join(root, 'manifest.webmanifest'), 'utf8'))
const sw = readFileSync(path.join(root, 'sw.js'), 'utf8')

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

test('manifest.webmanifest existiert und ist gültiges JSON', () => {
  assert.ok(manifest)
})

test('icons/Icon-192.png existiert', () => {
  readFileSync(path.join(root, 'icons', 'Icon-192.png'))
})

test('icons/Icon-512.png existiert', () => {
  readFileSync(path.join(root, 'icons', 'Icon-512.png'))
})

test('manifest hat Pflichtfelder name, short_name, start_url, icons', () => {
  assert.ok(manifest.name, 'name fehlt')
  assert.ok(manifest.short_name, 'short_name fehlt')
  assert.ok(manifest.start_url, 'start_url fehlt')
  assert.ok(Array.isArray(manifest.icons) && manifest.icons.length === 4, 'icons: 4 Einträge erwartet')
})

test('manifest hat Regular-Icons als any-Variant', () => {
  const anyIcons = manifest.icons.filter((icon) => icon.purpose === undefined || icon.purpose === 'any')
  assert.ok(anyIcons.length >= 2, `mindestens 2 any-Icons erwartet, gefunden: ${anyIcons.length}`)
})

test('manifest hat lang-Feld', () => {
  assert.ok(manifest.lang, 'lang-Feld fehlt im Manifest')
})

test('sw.js enthält install-Listener mit skipWaiting()', () => {
  assert.ok(sw.includes('install'), 'sw.js muss install-Events behandeln')
  assert.ok(sw.includes('skipWaiting()'), 'skipWaiting() fehlt')
})

test('sw.js enthält activate-Listener mit clients.claim()', () => {
  assert.ok(sw.includes('activate'), 'sw.js muss activate-Events behandeln')
  assert.ok(sw.includes('clients.claim()'), 'clients.claim() fehlt')
})

test('sw.js enthält fetch-Listener', () => {
  assert.ok(sw.includes('fetch'), 'sw.js muss fetch-Events behandeln')
})

test('sw.js enthält ignoreSearch:true', () => {
  assert.ok(
    /caches\.match\([^)]*ignoreSearch\s*:\s*true/.test(sw),
    'caches.match muss ignoreSearch:true verwenden'
  )
})

test('sw.js enthält Offline-Fallback mit HTTP 503', () => {
  assert.ok(sw.includes('.catch('), 'sw.js fetch braucht einen catch-Fallback')
  assert.ok(sw.includes('503'), 'Offline-Fallback muss HTTP 503 zurückgeben')
})

test('sw.js OFFLINE_ASSETS enthält Icon-Pfade', () => {
  assert.ok(sw.includes('Icon-192.png'), 'Icon-192.png muss in OFFLINE_ASSETS sein')
  assert.ok(sw.includes('Icon-512.png'), 'Icon-512.png muss in OFFLINE_ASSETS sein')
  assert.ok(sw.includes('Icon-maskable-192.png'), 'Icon-maskable-192.png muss in OFFLINE_ASSETS sein')
  assert.ok(sw.includes('Icon-maskable-512.png'), 'Icon-maskable-512.png muss in OFFLINE_ASSETS sein')
})

test('app.js importiert aus library.js', () => {
  const js = readFileSync(path.join(root, 'app.js'), 'utf8')
  assert.ok(js.includes('./library.js'), 'app.js muss aus ./library.js importieren')
})

test('saveProfile ist gegen localStorage-Fehler gesichert', () => {
  const js = readFileSync(path.join(root, 'app.js'), 'utf8')
  const fnStart = js.indexOf('function saveProfile(')
  assert.ok(fnStart !== -1, 'saveProfile muss existieren')
  const fnBody = js.slice(fnStart).split(/\n(?=function )/)[0]
  assert.ok(fnBody.includes('try'), 'saveProfile muss localStorage.setItem in try/catch wrappen')
  assert.ok(fnBody.includes('catch'), 'saveProfile braucht catch-Block')
})

test('package.json hat test-Script', () => {
  const pkg = JSON.parse(readFileSync(path.join(root, 'package.json'), 'utf8'))
  assert.ok(pkg.scripts?.test, 'package.json braucht scripts.test')
  assert.ok(pkg.scripts.test.includes('library.test.mjs'), 'test-Script muss library.test.mjs einschließen')
  assert.ok(pkg.scripts.test.includes('pwa.test.mjs'), 'test-Script muss pwa.test.mjs einschließen')
})

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

  test('KEIN apple-mobile-web-app-capable', () => {
    assert.doesNotMatch(html, /apple-mobile-web-app-capable/, 'deprecated und darf nicht gesetzt sein')
  })

  test('keine doppelten viewport-Meta-Tags', () => {
    const matches = html.match(/<meta[^>]*name="viewport"/g) ?? []
    assert.equal(matches.length, 1, `Genau 1 viewport-Meta erwartet, gefunden: ${matches.length}`)
  })

  test('theme-color Meta-Tag ist gesetzt', () => {
    assert.match(html, /<meta[^>]*name="theme-color"[^>]*content="[^"]+"/)
  })
})

describe('apple-touch-icon-180.png', () => {
  const iconPath = path.join(root, 'icons', 'apple-touch-icon-180.png')

  test('apple-touch-icon-180.png existiert', () => {
    assert.ok(existsSync(iconPath), 'icons/apple-touch-icon-180.png fehlt')
  })

  test('apple-touch-icon-180.png ist opak', () => {
    const result = execFileSync(
      'python',
      [
        '-c',
        'from PIL import Image; import sys; img=Image.open(sys.argv[1]); pixels=img.get_flattened_data() if hasattr(img, "get_flattened_data") else img.getdata(); print(sum(1 for px in pixels if len(px)==4 and px[3]==0))',
        iconPath,
      ],
      { encoding: 'utf8' }
    ).trim()
    assert.equal(result, '0', `apple-touch-icon-180.png hat transparente Pixel: ${result}`)
  })
})

describe('sw.js iOS- und Offline-Härtung', () => {
  test('CACHE_NAME ist v3 oder höher', () => {
    const match = sw.match(/CACHE_NAME\s*=\s*["']softwarecenter-companion-v(\d+)["']/)
    assert.ok(match && parseInt(match[1]) >= 3, 'CACHE_NAME muss v3+ sein')
  })

  test('apple-touch-icon-180.png ist in OFFLINE_ASSETS gecacht', () => {
    assert.ok(sw.includes('apple-touch-icon-180.png'), 'apple-touch-icon-180.png fehlt in OFFLINE_ASSETS')
  })
})
