/* Shared Admin behaviour. Page-specific controllers belong in separate files. */
document.addEventListener('DOMContentLoaded', () => {
  const sidebar = document.getElementById('sidebar');
  const menu = document.getElementById('adminMenuButton');
  const overlay = document.getElementById('adminSidebarOverlay');
  const main = document.getElementById('adminMain');
  const nav = sidebar?.querySelector('.sidebar-nav');
  if (!sidebar || !menu || !overlay || !nav) return;
  const media = window.matchMedia('(max-width: 768px)');
  let opened = false;
  const key = 'admin-sidebar-scroll';
  const remember = () => {
    try { sessionStorage.setItem(key, String(nav.scrollTop)); } catch {}
  };
  function icons() { if (window.lucide) window.lucide.createIcons(); }
  function setOpen(value, focus = true) {
    opened = Boolean(value && media.matches);
    sidebar.classList.toggle('open', opened);
    overlay.hidden = !opened;
    document.body.classList.toggle('admin-menu-open', opened);
    menu.setAttribute('aria-expanded', String(opened));
    menu.setAttribute('aria-label', opened ? 'Close sidebar' : 'Open sidebar');
    sidebar.inert = media.matches && !opened;
    if (main) main.inert = opened;
    if (focus && opened) (nav.querySelector('[aria-current="page"]') || nav.querySelector('a'))?.focus();
    else if (focus && media.matches) menu.focus();
  }
  function restore() {
    try {
      const saved = Number(sessionStorage.getItem(key));
      if (Number.isFinite(saved)) nav.scrollTop = saved;
    } catch {}
    const active = nav.querySelector('.sidebar-item.active');
    if (active) {
      const item = active.getBoundingClientRect(), area = nav.getBoundingClientRect();
      if (item.top < area.top) nav.scrollTop -= area.top - item.top;
      else if (item.bottom > area.bottom) nav.scrollTop += item.bottom - area.bottom;
    }
  }
  menu.addEventListener('click', () => setOpen(!opened));
  overlay.addEventListener('click', () => setOpen(false));
  document.addEventListener('keydown', event => {
    if (!opened) return;
    if (event.key === 'Escape') { event.preventDefault(); setOpen(false); }
    if (event.key !== 'Tab') return;
    const controls = [...sidebar.querySelectorAll('a[href],button:not(:disabled)')].filter(el => el.getClientRects().length);
    controls.push(menu);
    const first = controls[0], last = controls[controls.length - 1];
    if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
    else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
  });
  nav.querySelectorAll('a.sidebar-item').forEach(link => {
    if (link.classList.contains('active')) link.setAttribute('aria-current', 'page');
    link.addEventListener('click', remember);
  });
  nav.addEventListener('scroll', remember, {passive:true});
  media.addEventListener('change', () => setOpen(false, false));
  window.addEventListener('pagehide', remember);
  window.addEventListener('pageshow', () => { setOpen(false, false); requestAnimationFrame(restore); });
  setOpen(false, false);
  requestAnimationFrame(restore);
  icons();
});
