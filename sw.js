// Service worker do Gestão de Apostas: deixa o app instalável e abrindo mais rápido.
// - Página do app: sempre tenta a versão mais nova da internet; sem internet, usa a última salva.
// - Bibliotecas e fontes com versão fixa (Firebase, SheetJS, Google Fonts): guardadas e reaproveitadas.
// - Firebase (banco, login, IA) nunca passa pelo cache: vai direto para a internet.
const VERSION = 'v1';
const SHELL = 'apostas-shell-' + VERSION;
const LIBS = 'apostas-libs-' + VERSION;
const SHELL_FILES = ['/', '/manifest.webmanifest', '/icons/icon-192.png', '/icons/apple-touch-icon.png'];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(SHELL).then((c) => c.addAll(SHELL_FILES)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== SHELL && k !== LIBS).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

const isLib = (url) =>
  (url.hostname === 'www.gstatic.com' && url.pathname.startsWith('/firebasejs/')) ||
  url.hostname === 'cdnjs.cloudflare.com' ||
  url.hostname === 'fonts.googleapis.com' ||
  url.hostname === 'fonts.gstatic.com';

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);

  // Página e arquivos do próprio site: internet primeiro, cópia salva se estiver sem conexão.
  if (url.origin === self.location.origin) {
    e.respondWith(
      fetch(req)
        .then((res) => {
          if (res.ok && (req.mode === 'navigate' || SHELL_FILES.includes(url.pathname))) {
            const copy = res.clone();
            caches.open(SHELL).then((c) => c.put(req.mode === 'navigate' ? '/' : req, copy));
          }
          return res;
        })
        .catch(() => caches.match(req.mode === 'navigate' ? '/' : req).then((r) => r || caches.match('/')))
    );
    return;
  }

  // Bibliotecas com versão no endereço: usa a cópia salva e só baixa se não tiver.
  if (isLib(url)) {
    e.respondWith(
      caches.open(LIBS).then((c) =>
        c.match(req).then((hit) => hit || fetch(req).then((res) => {
          if (res.ok || res.type === 'opaque') c.put(req, res.clone());
          return res;
        }))
      )
    );
  }
  // Todo o resto (Firestore, login, Gemini, reCAPTCHA) segue direto, sem cache.
});
