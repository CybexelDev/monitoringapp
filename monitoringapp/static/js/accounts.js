/* Shared Accounts sidebar; no financial data is changed by this script. */
(() => {
  'use strict';
  window.lucide?.createIcons();
  const sidebar = document.getElementById('accountsSidebar');
  const button = document.getElementById('accountsMenuButton');
  const overlay = document.getElementById('accountsOverlay');
  const main = document.getElementById('accountsMain');
  const shell = document.querySelector('.accounts-shell');
  if (!sidebar || !button || !overlay || !main) return;
  const mobile = window.matchMedia('(max-width: 768px)');
  const nav = sidebar.querySelector('.accounts-nav');
  const key = 'accounts-sidebar-scroll';
  let opened = false;
  const saveScroll = () => { try { sessionStorage.setItem(key, String(nav.scrollTop)); } catch (_) {} };
  const restoreScroll = () => {
    try { const value = sessionStorage.getItem(key); if (value !== null && Number.isFinite(Number(value))) nav.scrollTop = Number(value); } catch (_) {}
    const active = nav.querySelector('.active');
    if (!active) return;
    active.setAttribute('aria-current', 'page');
    const item = active.getBoundingClientRect(), container = nav.getBoundingClientRect();
    if (item.top < container.top) nav.scrollTop -= container.top - item.top;
    if (item.bottom > container.bottom) nav.scrollTop += item.bottom - container.bottom;
  };
  function setOpen(value, focus = true) {
    opened = Boolean(value && mobile.matches);
    sidebar.classList.toggle('open', opened);
    sidebar.inert = mobile.matches && !opened;
    overlay.hidden = !opened;
    main.inert = opened;
    shell?.classList.toggle('drawer-locked', opened);
    button.setAttribute('aria-expanded', String(opened));
    button.setAttribute('aria-label', opened ? 'Close sidebar' : 'Open sidebar');
    if (opened && focus) sidebar.querySelector('a.accounts-nav-item')?.focus();
    if (!opened && focus && mobile.matches) button.focus();
  }
  button.addEventListener('click', () => setOpen(!opened));
  overlay.addEventListener('click', () => setOpen(false));
  document.addEventListener('keydown', event => {
    if (!opened) return;
    if (event.key === 'Escape') { event.preventDefault(); setOpen(false); }
    if (event.key !== 'Tab') return;
    const items = [button, ...sidebar.querySelectorAll('a[href], button:not(:disabled)')];
    const first = items[0], last = items[items.length - 1];
    if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
    else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
  });
  sidebar.querySelectorAll('a.accounts-nav-item').forEach(link => link.addEventListener('click', () => {
    saveScroll();
    if (mobile.matches) setOpen(false, false);
  }));
  nav.addEventListener('scroll', saveScroll, {passive: true});
  window.addEventListener('pagehide', saveScroll);
  window.addEventListener('pageshow', restoreScroll);
  mobile.addEventListener('change', () => setOpen(false, false));
  sidebar.querySelectorAll('.accounts-avatar img').forEach(image => image.addEventListener('error', () => {
    const avatar = image.parentElement;
    image.remove();
    avatar.textContent = 'A';
  }));
  setOpen(false, false);
  restoreScroll();
})();
