// Shared helpers for the dashboard.
const API = {
  async get(url) { const r = await fetch(url); if (!r.ok) throw new Error((await r.json()).error || r.statusText); return r.json(); },
  async post(url, body) {
    const r = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body || {}) });
    const data = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(data.error || r.statusText);
    return data;
  }
};

function toast(msg, kind) {
  const t = document.getElementById('toast');
  if (!t) return;
  t.textContent = msg;
  t.className = 'toast show ' + (kind || '');
  clearTimeout(window.__toastT);
  window.__toastT = setTimeout(() => { t.className = 'toast ' + (kind || ''); }, 3200);
}

const RECITER_ICONS = ['♪', '۞', '✦', '❖', '☾'];
function reciterIcon(i) { return RECITER_ICONS[i % RECITER_ICONS.length]; }

// Instagram status pill in the sidebar.
(async () => {
  const el = document.getElementById('ig-status');
  if (!el) return;
  try {
    const s = await API.get('/api/stats');
    if (s.instagram_ready) { el.className = 'pill pill-ok'; el.textContent = '● إنستجرام متصل'; }
    else { el.className = 'pill pill-warn'; el.textContent = '○ إنستجرام غير مهيأ'; }
  } catch (e) { el.className = 'pill pill-warn'; el.textContent = 'تعذّر الاتصال'; }
})();
