(() => {
  if (window.adminNotificationController) return;
  window.adminNotificationController = true;
  const link = document.getElementById('adminNotificationLink');
  if (!link) return;
  const endpoint = link.dataset.feedUrl;
  let folder = 'inbox', busy = false, timer, signature = '';
  const get = id => document.getElementById(id);
  function badge(count) {
    const node = get('adminNotificationBadge');
    if (node) { node.hidden = count === 0; node.textContent = count > 99 ? '99+' : String(count); node.setAttribute('aria-label', `${count} unread notifications`); }
  }
  function filter() {
    const search = get('notificationSearch');
    if (!search) return;
    const rows = [...document.querySelectorAll('.notification-row')];
    const matchesFolder = (row, f) => f === 'archived' ? row.dataset.archived === 'true' : row.dataset.archived !== 'true' && (f !== 'unread' || row.dataset.read === 'false');
    let shown = 0;
    rows.forEach(row => {
      row.hidden = !(matchesFolder(row, folder) && (!get('notificationKind').value || row.dataset.kind === get('notificationKind').value) && row.querySelector('.notification-content').textContent.toLowerCase().includes(search.value.trim().toLowerCase()));
      if (!row.hidden) shown++;
    });
    document.querySelectorAll('.notification-tab').forEach(tab => { tab.setAttribute('aria-pressed', String(tab.dataset.folder === folder)); tab.querySelector('span').textContent = rows.filter(row => matchesFolder(row, tab.dataset.folder)).length; });
    const scroll = document.querySelector('.notification-table-scroll');
    if (scroll) scroll.hidden = shown === 0;
    get('notificationNoMatch').hidden = shown > 0 || rows.length === 0;
    get('notificationResultCount').textContent = rows.length ? `${shown} notifications shown · Latest first` : '';
  }
  async function refresh(force = false) {
    if (busy || document.hidden) return;
    busy = true;
    try {
      const page = Boolean(get('notificationSearch'));
      const response = await fetch(endpoint + (page ? '' : '&counts=1'), {credentials:'same-origin', headers:{'X-Requested-With':'XMLHttpRequest'}, signal:AbortSignal.timeout(15000)});
      if (!response.ok) { if ([401,403].includes(response.status)) clearInterval(timer); return; }
      const data = await response.json();
      if (!data.ok) return;
      badge(data.unread_count);
      if (page && data.html) {
        const doc = new DOMParser().parseFromString(data.html, 'text/html');
        const incoming = doc.querySelector('.notification-shell');
        // Avoid replacing controls or rows when nothing changed.
        const newSignature = incoming.innerHTML;
        if (force || signature !== newSignature) {
          const shell = document.querySelector('.notification-shell');
          const position = shell.scrollTop;
          const oldScroll = shell.querySelector('.notification-table-scroll');
          const top = oldScroll?.scrollTop || 0, left = oldScroll?.scrollLeft || 0;
          const value = get('notificationSearch').value, kind = get('notificationKind').value;
          const activeId = document.activeElement?.id;
          const caret = get('notificationSearch').selectionStart;
          shell.innerHTML = incoming.innerHTML;
          get('notificationSearch').value = value; get('notificationKind').value = kind;
          const selected = shell.querySelector(`[data-value="${kind}"]`);
          if (selected) { get('categoryLabel').textContent = selected.textContent; shell.querySelectorAll('[data-value]').forEach(b=>b.classList.toggle('selected',b===selected)); }
          signature = newSignature; filter(); shell.scrollTop = position;
          const newScroll = shell.querySelector('.notification-table-scroll');
          if (newScroll) { newScroll.scrollTop = top; newScroll.scrollLeft = left; }
          if (activeId && get(activeId)) { get(activeId).focus({preventScroll:true}); if (activeId === 'notificationSearch' && caret !== null) { try { get(activeId).setSelectionRange(caret,caret); } catch {} } }
          if (window.lucide) window.lucide.createIcons();
        }
      }
    } catch (error) { if (force) alert('Could not update notifications. Please try again.'); }
    finally { busy = false; }
  }
  document.addEventListener('input', e => { if(e.target.id === 'notificationSearch') filter(); });
  document.addEventListener('change', e => { if(e.target.id === 'notificationKind') filter(); });
  document.addEventListener('click', e => {
    const tab = e.target.closest('.notification-tab');
    if(tab) { folder = tab.dataset.folder; filter(); }
    const category = e.target.closest('#categoryDropdown [data-value]');
    if(category) { get('notificationKind').value=category.dataset.value; get('categoryLabel').textContent=category.textContent; document.querySelectorAll('#categoryDropdown [data-value]').forEach(b=>b.classList.toggle('selected',b===category)); get('categoryDropdown').open=false; filter(); }
    const dropdown=get('categoryDropdown'); if(dropdown && !dropdown.contains(e.target)) dropdown.open=false;
    if(e.target.closest('[data-close-dialog]')) get('adminNotificationDialog').close();
  });
  document.addEventListener('keydown',e=> { if(e.key==='Escape' && get('categoryDropdown')) get('categoryDropdown').open=false; });
  document.addEventListener('submit', async e => {
    const form = e.target;
    if (!form.closest('.notification-shell')) return;
    e.preventDefault();
    if (busy) return;
    const button = e.submitter;
    const row = form.closest('.notification-row');
    const isView = Boolean(button?.classList.contains('notification-open'));
    const title = row?.querySelector('strong')?.textContent || '';
    const message = row?.querySelector('.notification-content p')?.textContent || '';
    busy = true; if(button) button.disabled=true;
    try {
      const response = await fetch(form.getAttribute('action'), {method:'POST', credentials:'same-origin', body:new FormData(form), headers:{'X-Requested-With':'XMLHttpRequest'}, signal:AbortSignal.timeout(15000)});
      const data = await response.json();
      if(!response.ok || !data.ok) throw new Error(data.message || 'Could not update notification.');
      badge(data.unread_count);
      if(isView) { get('adminNotificationTitle').textContent=title; get('adminNotificationMessage').textContent=message; get('adminNotificationDialog').showModal(); }
    } catch(error) { alert(error.message || 'Could not update notification.'); }
    finally { busy=false; if(button) button.disabled=false; await refresh(true); }
  });
  const dialog=get('adminNotificationDialog');
  if(dialog) { dialog.addEventListener('close',()=>document.body.style.overflow=''); dialog.addEventListener('click',e=> { if(e.target===dialog){const r=dialog.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)dialog.close();} }); }
  filter(); refresh(); timer=setInterval(refresh,10000);
  document.addEventListener('visibilitychange',()=> { if(!document.hidden) refresh(); });
  window.addEventListener('pagehide',()=>clearInterval(timer),{once:true});
})();
