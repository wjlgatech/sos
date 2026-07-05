---
name: installable-web-app
description: >-
  Give any web app a one-tap "Install" so it lands a permanent icon on a phone home
  screen, an iPad, or a Windows/Mac desktop and opens full-screen like a native app
  (a PWA) — plus double-click desktop shortcut files as a fallback. Framework-agnostic.
  Use when building/shipping ANY web UI, or when the user says "make it installable /
  add to home screen / desktop icon / don't lose the URL / PWA". Default practice for
  every agentic web app.
license: Proprietary
---

# Installable web app — a permanent icon on every device (the default)

**Why (the whole point):** a home-screen/desktop icon gets *opened again*; a bookmark or a
raw URL *rots and gets lost*. Making the app installable is the cheapest retention win there
is — a manifest, a few icons, ~4 routes. **Do this by default on every web app you ship.**

Rail A (the analogy): a food truck that only tweets its location vs. one with a permanent
stall in the market — the stall is the icon on the home screen. Rail B (the mechanism): a
**Web App Manifest** + **icons** + a trivial **service worker** turns a browser tab into an
installed app the OS pins.

## The universal recipe — 5 parts, framework-agnostic

Serve these four things and add head tags; the browser does the rest.

1. **`/manifest.webmanifest`** (JSON, `Content-Type: application/manifest+json`) — the app's
   identity: name, icons, `display:standalone`, colors, `start_url`.
2. **App icons** — from ONE square SVG, rasterized to PNG: `192`, `512`, a `512` **maskable**
   (full-bleed, content in the center 80% safe zone — the OS masks it), `apple-touch-icon`
   (180, opaque, no pre-rounded corners — iOS rounds it), and a `favicon` (48). Keep the mark
   **bold and simple** — ornate logos vanish at 192px.
3. **Head tags** — `<link rel="manifest">`, `<link rel="apple-touch-icon">`, `<meta name="theme-color">`,
   and the Apple set (`apple-mobile-web-app-capable`, `-status-bar-style`, `-title`), plus a
   `viewport` with `viewport-fit=cover`.
4. **`/sw.js`** — a minimal service worker whose ONLY job is to exist with a `fetch` listener
   (Chrome/Edge require it before showing the desktop **Install** button). **No caching.**
5. **Install affordance + desktop shortcuts** — a button that fires the native prompt where
   available, shows *Add to Home Screen* help on iOS, and offers double-click shortcut files
   (`.url` for Windows, `.webloc` for Mac) for every browser that has no prompt API.

## The three gotchas — baked in, so nobody re-learns them

1. **The service worker must NOT cache.** A caching SW on a frequently-updated app serves
   stale pages. Ship a bare fetch listener only (below). Add caching later, deliberately, with
   a versioned cache-bust — never by default.
2. **Static icons must ACTUALLY ship.** A real build drops non-code files. Verify the icons
   are in the *installed/bundled* artifact, not just the source tree:
   - Python setuptools → `[tool.setuptools.package-data] yourpkg=["static/*"]`; verify with
     `pip install . --target /tmp/x && ls /tmp/x/yourpkg/static`.
   - Node/bundlers → put icons in `public/`; verify they're in `dist/`.
   - **Curl the deployed icon** (`/static/icon-192.png` → 200 `image/png`, real bytes) — a
     404 here is the #1 silent PWA failure.
3. **Rasterizing needs a fallback chain.** No single tool is everywhere:
   ```bash
   raster() {  # in.svg  size  out.png
     if command -v rsvg-convert >/dev/null; then rsvg-convert -w "$2" -h "$2" "$1" -o "$3"
     elif python3 -c "import cairosvg" 2>/dev/null; then python3 -c "import cairosvg;cairosvg.svg2png(url='$1',write_to='$3',output_width=$2,output_height=$2)"
     elif command -v qlmanage >/dev/null; then d=$(dirname "$3");qlmanage -t -s "$2" -o "$d" "$1">/dev/null 2>&1;mv "$d/$(basename "$1").png" "$3"
     else echo "no rasterizer — ship icon.svg in the manifest (Chrome accepts SVG) + a placeholder PNG"; fi; }
   ```

## Copy-paste kit

**manifest.webmanifest**
```json
{ "name":"APP NAME","short_name":"APP","description":"…","start_url":"/?source=pwa",
  "scope":"/","display":"standalone","background_color":"#111","theme_color":"#111",
  "orientation":"portrait-primary",
  "icons":[
    {"src":"/static/icon.svg","sizes":"any","type":"image/svg+xml"},
    {"src":"/static/icon-192.png","sizes":"192x192","type":"image/png"},
    {"src":"/static/icon-512.png","sizes":"512x512","type":"image/png"},
    {"src":"/static/icon-512-maskable.png","sizes":"512x512","type":"image/png","purpose":"maskable"}
  ] }
```
**sw.js** (no caching)
```js
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil(self.clients.claim()));
self.addEventListener('fetch', () => {});
```
**head tags**
```html
<link rel="manifest" href="/manifest.webmanifest">
<meta name="theme-color" content="#111">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="APP">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
```
**install button JS** (native prompt → iOS help → shortcut downloads; no apostrophes in single-quoted strings if inside a server-templated page)
```js
(function(){ var b=document.getElementById("install"),h=document.getElementById("install-help");
 if("serviceWorker" in navigator)navigator.serviceWorker.register("/sw.js").catch(function(){});
 if(matchMedia("(display-mode: standalone)").matches||navigator.standalone)return;
 var ios=/iph|ipad|ipod/i.test(navigator.userAgent),d=null;
 addEventListener("beforeinstallprompt",function(e){e.preventDefault();d=e;b.style.display="";});
 if(ios)b.style.display="";
 b.onclick=function(){ if(d){d.prompt();d=null;b.style.display="none";return;} h.style.display="block"; };
 setTimeout(function(){ if(!d&&b.style.display==="none")b.style.display=""; },1400); })();
```
**Windows `.url`** (serve with `Content-Disposition: attachment; filename="APP.url"`)
```
[InternetShortcut]
URL=<the app base URL>
IconIndex=0
```
**Mac `.webloc`** (plist; `filename="APP.webloc"`)
```xml
<?xml version="1.0" encoding="UTF-8"?>
<plist version="1.0"><dict><key>URL</key><string><the app base URL></string></dict></plist>
```
> Build the base URL from the request (`X-Forwarded-Proto` + `Host`) so the shortcut opens
> *this* deployment, not a hardcoded host.

## Serving the 4 routes, per stack
- **Python `http.server`** — add `elif self.path=="/manifest.webmanifest": …` etc.; serve
  `Path(__file__).parent/"static"` basename-only.
- **Flask/FastAPI** — a static mount for `/static`, three tiny routes for manifest/sw/shortcut.
- **Express/Next/Vite** — icons in `public/`; `manifest.webmanifest` + `sw.js` are static files;
  a `/shortcut/:os` handler builds the file from the request host.
- **Static host (GitHub Pages/Netlify)** — all files are static; skip the dynamic shortcut route
  (or generate the `.url`/`.webloc` at build time with the known URL).

## Done test (both readers)
- A 15-year-old on a phone taps one button and gets an icon on their home screen.
- An engineer can point `curl` at `/manifest.webmanifest` (200, standalone, maskable icon) and
  `/static/icon-192.png` (200, real PNG bytes) on the **deployed** URL — not just localhost.

## Working exemplar
`song-of-songs` PR #36 — `sos/webapp.py` (manifest/sw/icon/shortcut routes + install button)
and `sos/static/` (the icon set), with the `package-data` fix and boot-a-real-server tests
(`tests/test_webapp.py::test_pwa_install_surface_serves_and_wires`). Copy that shape.
