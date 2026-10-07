/* Accounts bundle: each page controller exits when its page is absent.
   Order matters: clone edit fields before attaching shared calendar controls. */

/* Shared layout and sidebar */
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
  const saveScroll = () => { try { sessionStorage.setItem(key, String(nav?.scrollTop || 0)); } catch (_) {} };
  const restoreScroll = () => {
    if (!nav) return;
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
    document.body.classList.toggle('accounts-drawer-open', opened);
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
  nav?.addEventListener('scroll', saveScroll, {passive: true});
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
;

/* Income */
(() => {
  'use strict';
  const root = document.getElementById('accountsIncomePage');
  const form = document.getElementById('accountsIncomeForm');
  const button = document.getElementById('incomeSaveButton');
  const feedback = document.getElementById('incomeFeedback');
  const addDialog = document.getElementById('incomeAddDialog');
  const viewDialog = document.getElementById('incomeViewDialog');
  const historyDialog = document.getElementById('incomeHistoryDialog');
  const editDialog = document.getElementById('incomeEditDialog');
  const deleteDialog = document.getElementById('incomeDeleteDialog');
  const editForm = document.getElementById('incomeEditForm');
  const updateButton = document.getElementById('incomeUpdateButton');
  const deleteButton = document.getElementById('incomeDeleteButton');
  if (!root || !form || !button || !addDialog || !editDialog || !deleteDialog || !editForm || !updateButton || !deleteButton) return;
  let saving = false, loading = false, deleteUrl = '', opener = null;
  let scrollLocks = [];
  const busy = () => saving || loading;
  const csrf = () => form.elements.namedItem('csrfmiddlewaretoken').value;

  function notice(message, type = 'success') {
    if (typeof window.showToast === 'function') window.showToast(message, type);
    else if (feedback) {
      feedback.textContent = message; feedback.dataset.type = type; feedback.hidden = false;
    }
  }
  function clearErrors(targetForm, general) {
    general.hidden = true; general.textContent = '';
    const duplicateBox = targetForm.querySelector('.income-duplicate-box');
    if (duplicateBox) duplicateBox.hidden = true;
    targetForm.querySelectorAll('[data-field-error]').forEach(node => { node.textContent = ''; });
    targetForm.querySelectorAll('[aria-invalid]').forEach(node => {
      node.removeAttribute('aria-invalid'); node.removeAttribute('aria-describedby');
    });
  }
  function showErrors(targetForm, general, errors) {
    let first;
    Object.entries(errors || {}).forEach(([name, values]) => {
      const text = values.map(value => value.message).join(' ');
      const target = [...targetForm.querySelectorAll('[data-field-error]')].find(node => node.dataset.fieldError === name);
      const field = targetForm.elements.namedItem(name);
      if (target && field) {
        target.textContent = text; field.setAttribute('aria-invalid', 'true');
        field.setAttribute('aria-describedby', target.id); first ||= field;
      } else { general.textContent += `${text} `; general.hidden = false; }
    });
    first?.focus();
  }
  async function requestJson(url, options = {}) {
    const response = await fetch(url, {credentials: 'same-origin', cache: 'no-store', ...options});
    if (!(response.headers.get('content-type') || '').includes('application/json')) {
      throw new Error('Unexpected response. Check your session and income list before trying again.');
    }
    const data = await response.json();
    if (options.method === 'POST' && response.ok && data.ok) {
      document.dispatchEvent(new CustomEvent('accounts:notifications-refresh'));
    }
    return {response, data};
  }
  const postOptions = body => ({
    method: 'POST', headers: {'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': csrf()}, body
  });
  async function refreshSnapshot(url, historyMode, silent = false) {
    if (loading) return false;
    loading = true; root.setAttribute('aria-busy', 'true');
    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 15000);
      let response;
      try { response = await fetch(url, {credentials: 'same-origin', cache: 'no-store', signal: controller.signal}); }
      finally { clearTimeout(timeout); }
      if (!response.ok && response.status !== 400) throw new Error('Income list could not be loaded.');
      const page = new DOMParser().parseFromString(await response.text(), 'text/html');
      const snapshot = page.getElementById('incomeSnapshot');
      if (!snapshot) throw new Error('Income list unavailable. Sign in again if your session has ended.');
      if (silent && (saving || document.hidden || document.querySelector('dialog[open]') || root.contains(document.activeElement))) return false;
      const current = document.getElementById('incomeSnapshot');
      const positions = [...current.querySelectorAll('[class*=table-scroll]')].map(node => ({top: node.scrollTop, left: node.scrollLeft}));
      current.replaceWith(snapshot);
      snapshot.querySelectorAll('[class*=table-scroll]').forEach((node, index) => {
        if (positions[index]) {node.scrollTop = positions[index].top; node.scrollLeft = positions[index].left;}
      });
      if (historyMode === 'push') history.pushState(null, '', url);
      if (historyMode === 'replace') history.replaceState(null, '', url);
      window.lucide?.createIcons();
      return true;
    } catch (error) { if (!silent) notice(error.message, 'error'); return false; }
    finally { loading = false; root.removeAttribute('aria-busy'); }
  }
  function openPopup(dialog, trigger) {
    opener = trigger;
    scrollLocks = [...new Set([document.documentElement, document.body, ...document.querySelectorAll('.accounts-shell, .accounts-main')])]
      .map(node => ({node, value: node.style.getPropertyValue('overflow'), priority: node.style.getPropertyPriority('overflow')}));
    scrollLocks.forEach(({node}) => node.style.setProperty('overflow', 'hidden', 'important'));
    dialog.showModal(); window.lucide?.createIcons();
  }
  function restoreScroll() {
    scrollLocks.forEach(({node, value, priority}) => {
      if (value) node.style.setProperty('overflow', value, priority);
      else node.style.removeProperty('overflow');
    });
    scrollLocks = [];
    if (opener?.isConnected) opener.focus();
    else document.getElementById('incomeSearch')?.focus();
    opener = null;
  }
  [addDialog, editDialog, deleteDialog, viewDialog, historyDialog].filter(Boolean).forEach(dialog => {
    dialog.addEventListener('close', restoreScroll);
    dialog.addEventListener('cancel', event => { if (saving) event.preventDefault(); });
    dialog.addEventListener('click', event => {
      if (saving) return;
      if (event.target.closest('[data-income-close]')) dialog.close();
      else if (event.target === dialog) {
        const bounds = dialog.getBoundingClientRect();
        if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) dialog.close();
      }
    });
  });
  function setModalBusy(dialog, value) {
    dialog.querySelectorAll('button').forEach(node => { node.disabled = value; });
    dialog.setAttribute('aria-busy', String(value));
  }
  if (addDialog.dataset.formErrors === '1') openPopup(addDialog, document.getElementById('incomeAddButton'));
  // Clone the validated Add fields once, with separate IDs for the edit popup.
  const fields = form.querySelector('.income-form-grid').cloneNode(true);
  fields.querySelectorAll('[id]').forEach(node => { node.id = `edit_${node.id}`; });
  fields.querySelectorAll('label[for]').forEach(node => { node.htmlFor = `edit_${node.htmlFor}`; });
  fields.querySelectorAll('[aria-describedby]').forEach(node => node.removeAttribute('aria-describedby'));
  document.getElementById('incomeEditFields').replaceWith(fields);


  function showDuplicate(targetForm, data) {
    if (!data.duplicate) return false;
    const box = targetForm.querySelector('.income-duplicate-box');
    box.querySelector('[data-income-duplicate-message]').textContent = data.message;
    box.hidden = false;
    box.querySelector('[data-income-duplicate-confirm]').focus();
    return true;
  }
  [form, editForm].forEach(targetForm => {
    targetForm.addEventListener('input', () => {
      targetForm.elements.namedItem('confirm_duplicate').value = '0';
      targetForm.querySelector('.income-duplicate-box').hidden = true;
    });
    targetForm.addEventListener('click', event => {
      if (event.target.closest('[data-income-duplicate-confirm]')) {
        targetForm.elements.namedItem('confirm_duplicate').value = '1';
        targetForm.requestSubmit();
      }
      if (event.target.closest('[data-income-duplicate-cancel]')) {
        targetForm.querySelector('.income-duplicate-box').hidden = true;
        targetForm.elements.namedItem('confirm_duplicate').value = '0';
        targetForm.elements.namedItem('reference').focus();
      }
    });
  });

  form.addEventListener('submit', async event => {
    event.preventDefault(); if (busy()) return;
    saving = true; setModalBusy(addDialog, true);
    const general = document.getElementById('incomeFormError'); clearErrors(form, general);
    const label = button.querySelector('span'); label.textContent = 'Saving…';
    try {
      const {response, data} = await requestJson((form.getAttribute('action') || location.href), postOptions(new FormData(form)));
      if (!response.ok || !data.ok) {
        if (showDuplicate(form, data)) return;
        showErrors(form, general, data.errors); notice(data.message || 'Income could not be saved.', 'error'); return;
      }
      form.reset(); addDialog.close(); notice(data.message || 'Income saved successfully.');
      if (!await refreshSnapshot(location.href, 'replace')) {
        notice('Income was saved. Reload the list to see the new entry.', 'warning');
      }
    } catch (error) { notice(error.message || 'Unable to confirm the save. Check the list before submitting again.', 'error'); }
    finally { saving = false; setModalBusy(addDialog, false); label.textContent = 'Save Income'; }
  });
  root.addEventListener('change', event => {
    if (event.target.id !== 'incomePeriod') return;
    root.querySelectorAll('[data-income-period]').forEach(node => {
      node.hidden = node.dataset.incomePeriod !== event.target.value;
    });
  });
  root.addEventListener('submit', async event => {
    if (event.target.id !== 'incomeSearchForm') return;
    event.preventDefault(); if (busy()) return;
    const url = new URL((event.target.getAttribute('action') || location.href), location.href);
    const filters = new FormData(event.target);
    for (const [name, value] of filters) url.searchParams.set(name, value);
    if (event.submitter?.name !== 'export') { refreshSnapshot(url, 'push'); return; }
    url.searchParams.set('export', 'xlsx');
    loading = true;
    const exportButton = event.submitter; exportButton.disabled = true;
    const exportLabel = exportButton.querySelector('span');
    if (exportLabel) exportLabel.textContent = 'Exporting…';
    root.setAttribute('aria-busy', 'true');
    try {
      const response = await fetch(url, {credentials: 'same-origin', cache: 'no-store'});
      if (!response.ok || !(response.headers.get('content-type') || '').includes('spreadsheetml')) {
        if (response.status === 400) {
          const errorPage = new DOMParser().parseFromString(await response.text(), 'text/html');
          const message = errorPage.querySelector('.income-form-error')?.textContent.trim();
          throw new Error(message || 'Check the selected dates and try exporting again.');
        }
        throw new Error('Export could not be downloaded. Check your session and filters.');
      }
      const blobUrl = URL.createObjectURL(await response.blob());
      const link = document.createElement('a'); link.href = blobUrl;
      const filename = (response.headers.get('content-disposition') || '').match(/filename="([^"]+)"/);
      link.download = filename ? filename[1] : 'income.xlsx';
      document.body.append(link); link.click(); link.remove();
      setTimeout(() => URL.revokeObjectURL(blobUrl), 10000);
      notice('Excel download started.');
    } catch (error) { notice(error.message, 'error'); }
    finally {
      loading = false; exportButton.disabled = false; root.removeAttribute('aria-busy');
      if (exportLabel) exportLabel.textContent = 'Export to Excel';
    }
  });
  root.addEventListener('click', async event => {
    const history = event.target.closest('[data-income-history]');
    if (history) {
      if (busy() || !historyDialog) return;
      loading = true; history.disabled = true;
      try {
        const {response, data} = await requestJson(history.dataset.incomeHistory);
        if (!response.ok || !data.ok) throw new Error(data.message || 'History could not be loaded.');
        const content = document.getElementById('incomeHistoryContent');
        content.replaceChildren();
        const labels = {date:'Date', category:'Category', amount:'Amount', payment_method:'Payment method', reference:'Reference', description:'Description', receipt:'Receipt'};
        if (!data.items.length) content.textContent = 'No changes recorded yet.';
        data.items.forEach(item => {
          const card = document.createElement('article'); card.className = 'income-history-card';
          const heading = document.createElement('h3'); heading.textContent = `${item.action} · ${item.actor}`;
          const time = document.createElement('time'); time.textContent = item.time;
          card.append(heading, time);
          Object.entries(item.changes).forEach(([key, value]) => {
            const line = document.createElement('p');
            line.textContent = `${labels[key] || key}: ${value.before || '—'} → ${value.after || '—'}`;
            card.append(line);
          });
          content.append(card);
        });
        openPopup(historyDialog, history);
      } catch (error) { notice(error.message, 'error'); }
      finally { loading = false; history.disabled = false; }
      return;
    }
    const view = event.target.closest('[data-income-view]');
    if (view) {
      if (busy() || !viewDialog) return;
      const details = view.closest('tr')?.querySelector('.income-view-template');
      if (!details) { notice('Income details are unavailable.', 'error'); return; }
      document.getElementById('incomeViewContent').replaceChildren(details.content.cloneNode(true));
      openPopup(viewDialog, view);
      return;
    }
    const add = event.target.closest('#incomeAddButton');
    if (add) { if (!busy()) openPopup(addDialog, add); return; }
    const link = event.target.closest('a[data-income-page]');
    if (link) {
      if (event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
      event.preventDefault(); if (!busy()) refreshSnapshot(link.href, 'push'); return;
    }
    const edit = event.target.closest('[data-income-edit]');
    const remove = event.target.closest('[data-income-delete]');
    if ((!edit && !remove) || busy()) return;
    if (remove) {
      deleteUrl = remove.dataset.incomeDelete;
      document.getElementById('incomeDeleteCategory').textContent = remove.dataset.incomeCategory || 'this entry';
      document.getElementById('incomeDeleteError').hidden = true;
      openPopup(deleteDialog, remove); return;
    }
    loading = true; edit.disabled = true;
    try {
      const {response, data} = await requestJson(edit.dataset.incomeEdit);
      if (!response.ok || !data.ok) { notice(data.message || 'Income could not be opened.', 'error'); return; }
      editForm.reset(); clearErrors(editForm, document.getElementById('incomeEditError'));
      editForm.action = edit.dataset.incomeEdit;
      Object.entries(data.item).forEach(([name, value]) => {
        const field = editForm.elements.namedItem(name); if (field) field.value = value ?? '';
      });
      const receiptBox = document.getElementById('incomeCurrentReceipt');
      receiptBox.hidden = !data.receipt_url;
      if (data.receipt_url) receiptBox.querySelector('a').href = data.receipt_url;
      openPopup(editDialog, edit);
    } catch (error) { notice(error.message || 'Income could not be opened.', 'error'); }
    finally { loading = false; edit.disabled = false; }
  });
  editForm.addEventListener('submit', async event => {
    event.preventDefault(); if (busy()) return;
    saving = true; setModalBusy(editDialog, true); updateButton.textContent = 'Saving…';
    const general = document.getElementById('incomeEditError'); clearErrors(editForm, general);
    try {
      const {response, data} = await requestJson(editForm.action, postOptions(new FormData(editForm)));
      if (!response.ok || !data.ok) {
        if (showDuplicate(editForm, data)) return;
        showErrors(editForm, general, data.errors); general.textContent ||= data.message || 'Update failed.'; general.hidden = false; return;
      }
      editDialog.close(); notice(data.message || 'Income updated successfully.');
      if (!await refreshSnapshot(location.href, 'replace')) notice('Income updated. Reload the list to see the changes.', 'warning');
    } catch (_) {
      general.textContent = 'Unable to confirm the update. Close this popup and check the list before retrying.'; general.hidden = false;
    } finally { saving = false; setModalBusy(editDialog, false); updateButton.textContent = 'Save Changes'; }
  });
  deleteButton.addEventListener('click', async () => {
    if (busy() || !deleteUrl) return;
    saving = true; setModalBusy(deleteDialog, true); deleteButton.textContent = 'Deleting…';
    const general = document.getElementById('incomeDeleteError'); general.hidden = true;
    try {
      const deleteData = new URLSearchParams();
      deleteData.set('csrfmiddlewaretoken', csrf());
      const {response, data} = await requestJson(deleteUrl, postOptions(deleteData));
      if (!response.ok || !data.ok) { general.textContent = data.message || 'Delete failed.'; general.hidden = false; return; }
      deleteDialog.close(); notice(data.message || 'Income deleted successfully.'); deleteUrl = '';
      if (!await refreshSnapshot(location.href, 'replace')) notice('Income deleted. Reload the list to see the changes.', 'warning');
    } catch (_) {
      general.textContent = 'Unable to confirm deletion. Close this popup and check the list before retrying.'; general.hidden = false;
    } finally { saving = false; setModalBusy(deleteDialog, false); deleteButton.textContent = 'Delete Income'; }
  });
  function refreshLiveList() {
    if (!root.isConnected || document.hidden || busy() || document.querySelector('dialog[open]') || root.contains(document.activeElement)) return;
    refreshSnapshot(location.href, undefined, true);
  }
  const liveTimer = setInterval(() => {
    if (!root.isConnected) { clearInterval(liveTimer); return; }
    refreshLiveList();
  }, 15000);
  document.addEventListener('visibilitychange', refreshLiveList);
  window.addEventListener('focus', refreshLiveList);
  window.addEventListener('popstate', () => {
    if (root.isConnected && !busy()) {
      [addDialog, editDialog, deleteDialog, viewDialog, historyDialog].filter(Boolean).forEach(dialog => { if (dialog.open) dialog.close(); });
      refreshSnapshot(location.href);
    }
  });
})();
;

/* Expenses */
(() => {
  'use strict';
  const root = document.getElementById('accountsExpensePage');
  const form = document.getElementById('accountsExpenseForm');
  const button = document.getElementById('expenseSaveButton');
  const feedback = document.getElementById('expenseFeedback');
  const addDialog = document.getElementById('expenseAddDialog');
  const viewDialog = document.getElementById('expenseViewDialog');
  const historyDialog = document.getElementById('expenseHistoryDialog');
  const editDialog = document.getElementById('expenseEditDialog');
  const deleteDialog = document.getElementById('expenseDeleteDialog');
  const editForm = document.getElementById('expenseEditForm');
  const updateButton = document.getElementById('expenseUpdateButton');
  const deleteButton = document.getElementById('expenseDeleteButton');
  if (!root || !form || !button || !addDialog || !editDialog || !deleteDialog || !editForm || !updateButton || !deleteButton) return;
  let saving = false, loading = false, deleteUrl = '', opener = null;
  let scrollLocks = [];
  const busy = () => saving || loading;
  const csrf = () => form.elements.namedItem('csrfmiddlewaretoken').value;

  function notice(message, type = 'success') {
    if (typeof window.showToast === 'function') window.showToast(message, type);
    else if (feedback) {
      feedback.textContent = message; feedback.dataset.type = type; feedback.hidden = false;
    }
  }
  function clearErrors(targetForm, general) {
    general.hidden = true; general.textContent = '';
    const duplicateBox = targetForm.querySelector('.expense-duplicate-box');
    if (duplicateBox) duplicateBox.hidden = true;
    targetForm.querySelectorAll('[data-field-error]').forEach(node => { node.textContent = ''; });
    targetForm.querySelectorAll('[aria-invalid]').forEach(node => {
      node.removeAttribute('aria-invalid'); node.removeAttribute('aria-describedby');
    });
  }
  function showErrors(targetForm, general, errors) {
    let first;
    Object.entries(errors || {}).forEach(([name, values]) => {
      const text = values.map(value => value.message).join(' ');
      const target = [...targetForm.querySelectorAll('[data-field-error]')].find(node => node.dataset.fieldError === name);
      const field = targetForm.elements.namedItem(name);
      if (target && field) {
        target.textContent = text; field.setAttribute('aria-invalid', 'true');
        field.setAttribute('aria-describedby', target.id); first ||= field;
      } else { general.textContent += `${text} `; general.hidden = false; }
    });
    first?.focus();
  }
  async function requestJson(url, options = {}) {
    const response = await fetch(url, {credentials: 'same-origin', cache: 'no-store', ...options});
    if (!(response.headers.get('content-type') || '').includes('application/json')) {
      throw new Error('Unexpected response. Check your session and expense list before trying again.');
    }
    const data = await response.json();
    if (options.method === 'POST' && response.ok && data.ok) {
      document.dispatchEvent(new CustomEvent('accounts:notifications-refresh'));
    }
    return {response, data};
  }
  const postOptions = body => ({
    method: 'POST', headers: {'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': csrf()}, body
  });
  async function refreshSnapshot(url, historyMode, silent = false) {
    if (loading) return false;
    loading = true; root.setAttribute('aria-busy', 'true');
    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 15000);
      let response;
      try { response = await fetch(url, {credentials: 'same-origin', cache: 'no-store', signal: controller.signal}); }
      finally { clearTimeout(timeout); }
      if (!response.ok && response.status !== 400) throw new Error('Expense list could not be loaded.');
      const page = new DOMParser().parseFromString(await response.text(), 'text/html');
      const snapshot = page.getElementById('expenseSnapshot');
      if (!snapshot) throw new Error('Expense list unavailable. Sign in again if your session has ended.');
      if (silent && (saving || document.hidden || document.querySelector('dialog[open]') || root.contains(document.activeElement))) return false;
      const current = document.getElementById('expenseSnapshot');
      const positions = [...current.querySelectorAll('[class*=table-scroll]')].map(node => ({top: node.scrollTop, left: node.scrollLeft}));
      current.replaceWith(snapshot);
      snapshot.querySelectorAll('[class*=table-scroll]').forEach((node, index) => {
        if (positions[index]) {node.scrollTop = positions[index].top; node.scrollLeft = positions[index].left;}
      });
      if (historyMode === 'push') history.pushState(null, '', url);
      if (historyMode === 'replace') history.replaceState(null, '', url);
      window.lucide?.createIcons();
      return true;
    } catch (error) { if (!silent) notice(error.message, 'error'); return false; }
    finally { loading = false; root.removeAttribute('aria-busy'); }
  }
  function openPopup(dialog, trigger) {
    opener = trigger;
    scrollLocks = [...new Set([document.documentElement, document.body, ...document.querySelectorAll('.accounts-shell, .accounts-main')])]
      .map(node => ({node, value: node.style.getPropertyValue('overflow'), priority: node.style.getPropertyPriority('overflow')}));
    scrollLocks.forEach(({node}) => node.style.setProperty('overflow', 'hidden', 'important'));
    dialog.showModal(); window.lucide?.createIcons();
  }
  function restoreScroll() {
    scrollLocks.forEach(({node, value, priority}) => {
      if (value) node.style.setProperty('overflow', value, priority);
      else node.style.removeProperty('overflow');
    });
    scrollLocks = [];
    if (opener?.isConnected) opener.focus();
    else document.getElementById('expenseSearch')?.focus();
    opener = null;
  }
  [addDialog, editDialog, deleteDialog, viewDialog, historyDialog].filter(Boolean).forEach(dialog => {
    dialog.addEventListener('close', restoreScroll);
    dialog.addEventListener('cancel', event => { if (saving) event.preventDefault(); });
    dialog.addEventListener('click', event => {
      if (saving) return;
      if (event.target.closest('[data-expense-close]')) dialog.close();
      else if (event.target === dialog) {
        const bounds = dialog.getBoundingClientRect();
        if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) dialog.close();
      }
    });
  });
  function setModalBusy(dialog, value) {
    dialog.querySelectorAll('button').forEach(node => { node.disabled = value; });
    dialog.setAttribute('aria-busy', String(value));
  }
  if (addDialog.dataset.formErrors === '1') openPopup(addDialog, document.getElementById('expenseAddButton'));
  // Clone the validated Add fields once, with separate IDs for the edit popup.
  const fields = form.querySelector('.expense-form-grid').cloneNode(true);
  fields.querySelectorAll('[id]').forEach(node => { node.id = `edit_${node.id}`; });
  fields.querySelectorAll('label[for]').forEach(node => { node.htmlFor = `edit_${node.htmlFor}`; });
  fields.querySelectorAll('[aria-describedby]').forEach(node => node.removeAttribute('aria-describedby'));
  document.getElementById('expenseEditFields').replaceWith(fields);


  function showDuplicate(targetForm, data) {
    if (!data.duplicate) return false;
    const box = targetForm.querySelector('.expense-duplicate-box');
    box.querySelector('[data-expense-duplicate-message]').textContent = data.message;
    box.hidden = false;
    box.querySelector('[data-expense-duplicate-confirm]').focus();
    return true;
  }
  [form, editForm].forEach(targetForm => {
    targetForm.addEventListener('input', () => {
      targetForm.elements.namedItem('confirm_duplicate').value = '0';
      targetForm.querySelector('.expense-duplicate-box').hidden = true;
    });
    targetForm.addEventListener('click', event => {
      if (event.target.closest('[data-expense-duplicate-confirm]')) {
        targetForm.elements.namedItem('confirm_duplicate').value = '1';
        targetForm.requestSubmit();
      }
      if (event.target.closest('[data-expense-duplicate-cancel]')) {
        targetForm.querySelector('.expense-duplicate-box').hidden = true;
        targetForm.elements.namedItem('confirm_duplicate').value = '0';
        targetForm.elements.namedItem('reference').focus();
      }
    });
  });

  form.addEventListener('submit', async event => {
    event.preventDefault(); if (busy()) return;
    saving = true; setModalBusy(addDialog, true);
    const general = document.getElementById('expenseFormError'); clearErrors(form, general);
    const label = button.querySelector('span'); label.textContent = 'Saving…';
    try {
      const {response, data} = await requestJson((form.getAttribute('action') || location.href), postOptions(new FormData(form)));
      if (!response.ok || !data.ok) {
        if (showDuplicate(form, data)) return;
        showErrors(form, general, data.errors); notice(data.message || 'Expense could not be saved.', 'error'); return;
      }
      form.reset(); addDialog.close(); notice(data.message || 'Expense saved successfully.');
      if (!await refreshSnapshot(location.href, 'replace')) {
        notice('Expense was saved. Reload the list to see the new entry.', 'warning');
      }
    } catch (error) { notice(error.message || 'Unable to confirm the save. Check the list before submitting again.', 'error'); }
    finally { saving = false; setModalBusy(addDialog, false); label.textContent = 'Save Expense'; }
  });
  root.addEventListener('change', event => {
    if (event.target.id !== 'expensePeriod') return;
    root.querySelectorAll('[data-expense-period]').forEach(node => {
      node.hidden = node.dataset.expensePeriod !== event.target.value;
    });
  });
  root.addEventListener('submit', async event => {
    if (event.target.id !== 'expenseSearchForm') return;
    event.preventDefault(); if (busy()) return;
    const url = new URL((event.target.getAttribute('action') || location.href), location.href);
    const filters = new FormData(event.target);
    for (const [name, value] of filters) url.searchParams.set(name, value);
    if (event.submitter?.name !== 'export') { refreshSnapshot(url, 'push'); return; }
    url.searchParams.set('export', 'xlsx');
    loading = true;
    const exportButton = event.submitter; exportButton.disabled = true;
    const exportLabel = exportButton.querySelector('span');
    if (exportLabel) exportLabel.textContent = 'Exporting…';
    root.setAttribute('aria-busy', 'true');
    try {
      const response = await fetch(url, {credentials: 'same-origin', cache: 'no-store'});
      if (!response.ok || !(response.headers.get('content-type') || '').includes('spreadsheetml')) {
        if (response.status === 400) {
          const errorPage = new DOMParser().parseFromString(await response.text(), 'text/html');
          const message = errorPage.querySelector('.expense-form-error')?.textContent.trim();
          throw new Error(message || 'Check the selected dates and try exporting again.');
        }
        throw new Error('Export could not be downloaded. Check your session and filters.');
      }
      const blobUrl = URL.createObjectURL(await response.blob());
      const link = document.createElement('a'); link.href = blobUrl;
      const filename = (response.headers.get('content-disposition') || '').match(/filename="([^"]+)"/);
      link.download = filename ? filename[1] : 'expense.xlsx';
      document.body.append(link); link.click(); link.remove();
      setTimeout(() => URL.revokeObjectURL(blobUrl), 10000);
      notice('Excel download started.');
    } catch (error) { notice(error.message, 'error'); }
    finally {
      loading = false; exportButton.disabled = false; root.removeAttribute('aria-busy');
      if (exportLabel) exportLabel.textContent = 'Export to Excel';
    }
  });
  root.addEventListener('click', async event => {
    const history = event.target.closest('[data-expense-history]');
    if (history) {
      if (busy() || !historyDialog) return;
      loading = true; history.disabled = true;
      try {
        const {response, data} = await requestJson(history.dataset.expenseHistory);
        if (!response.ok || !data.ok) throw new Error(data.message || 'History could not be loaded.');
        const content = document.getElementById('expenseHistoryContent');
        content.replaceChildren();
        const labels = {date:'Date', category:'Category', amount:'Total amount', paid_amount:'Paid amount', paid_to:'Paid to', payment_method:'Payment method', reference:'Reference', description:'Description', receipt:'Receipt'};
        if (!data.items.length) content.textContent = 'No changes recorded yet.';
        data.items.forEach(item => {
          const card = document.createElement('article'); card.className = 'expense-history-card';
          const heading = document.createElement('h3'); heading.textContent = `${item.action} · ${item.actor}`;
          const time = document.createElement('time'); time.textContent = item.time;
          card.append(heading, time);
          Object.entries(item.changes).forEach(([key, value]) => {
            const line = document.createElement('p');
            line.textContent = `${labels[key] || key}: ${value.before || '—'} → ${value.after || '—'}`;
            card.append(line);
          });
          content.append(card);
        });
        openPopup(historyDialog, history);
      } catch (error) { notice(error.message, 'error'); }
      finally { loading = false; history.disabled = false; }
      return;
    }
    const view = event.target.closest('[data-expense-view]');
    if (view) {
      if (busy() || !viewDialog) return;
      const details = view.closest('tr')?.querySelector('.expense-view-template');
      if (!details) { notice('Expense details are unavailable.', 'error'); return; }
      document.getElementById('expenseViewContent').replaceChildren(details.content.cloneNode(true));
      openPopup(viewDialog, view);
      return;
    }
    const add = event.target.closest('#expenseAddButton');
    if (add) { if (!busy()) openPopup(addDialog, add); return; }
    const link = event.target.closest('a[data-expense-page]');
    if (link) {
      if (event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
      event.preventDefault(); if (!busy()) refreshSnapshot(link.href, 'push'); return;
    }
    const edit = event.target.closest('[data-expense-edit]');
    const remove = event.target.closest('[data-expense-delete]');
    if ((!edit && !remove) || busy()) return;
    if (remove) {
      deleteUrl = remove.dataset.expenseDelete;
      document.getElementById('expenseDeleteCategory').textContent = remove.dataset.expenseCategory || 'this entry';
      document.getElementById('expenseDeleteError').hidden = true;
      openPopup(deleteDialog, remove); return;
    }
    loading = true; edit.disabled = true;
    try {
      const {response, data} = await requestJson(edit.dataset.expenseEdit);
      if (!response.ok || !data.ok) { notice(data.message || 'Expense could not be opened.', 'error'); return; }
      editForm.reset(); clearErrors(editForm, document.getElementById('expenseEditError'));
      editForm.action = edit.dataset.expenseEdit;
      Object.entries(data.item).forEach(([name, value]) => {
        const field = editForm.elements.namedItem(name); if (field) field.value = value ?? '';
      });
      const receiptBox = document.getElementById('expenseCurrentReceipt');
      receiptBox.hidden = !data.receipt_url;
      if (data.receipt_url) receiptBox.querySelector('a').href = data.receipt_url;
      openPopup(editDialog, edit);
    } catch (error) { notice(error.message || 'Expense could not be opened.', 'error'); }
    finally { loading = false; edit.disabled = false; }
  });
  editForm.addEventListener('submit', async event => {
    event.preventDefault(); if (busy()) return;
    saving = true; setModalBusy(editDialog, true); updateButton.textContent = 'Saving…';
    const general = document.getElementById('expenseEditError'); clearErrors(editForm, general);
    try {
      const {response, data} = await requestJson(editForm.action, postOptions(new FormData(editForm)));
      if (!response.ok || !data.ok) {
        if (showDuplicate(editForm, data)) return;
        showErrors(editForm, general, data.errors); general.textContent ||= data.message || 'Update failed.'; general.hidden = false; return;
      }
      editDialog.close(); notice(data.message || 'Expense updated successfully.');
      if (!await refreshSnapshot(location.href, 'replace')) notice('Expense updated. Reload the list to see the changes.', 'warning');
    } catch (_) {
      general.textContent = 'Unable to confirm the update. Close this popup and check the list before retrying.'; general.hidden = false;
    } finally { saving = false; setModalBusy(editDialog, false); updateButton.textContent = 'Save Changes'; }
  });
  deleteButton.addEventListener('click', async () => {
    if (busy() || !deleteUrl) return;
    saving = true; setModalBusy(deleteDialog, true); deleteButton.textContent = 'Deleting…';
    const general = document.getElementById('expenseDeleteError'); general.hidden = true;
    try {
      const deleteData = new URLSearchParams();
      deleteData.set('csrfmiddlewaretoken', csrf());
      const {response, data} = await requestJson(deleteUrl, postOptions(deleteData));
      if (!response.ok || !data.ok) { general.textContent = data.message || 'Delete failed.'; general.hidden = false; return; }
      deleteDialog.close(); notice(data.message || 'Expense deleted successfully.'); deleteUrl = '';
      if (!await refreshSnapshot(location.href, 'replace')) notice('Expense deleted. Reload the list to see the changes.', 'warning');
    } catch (_) {
      general.textContent = 'Unable to confirm deletion. Close this popup and check the list before retrying.'; general.hidden = false;
    } finally { saving = false; setModalBusy(deleteDialog, false); deleteButton.textContent = 'Delete Expense'; }
  });
  function refreshLiveList() {
    if (!root.isConnected || document.hidden || busy() || document.querySelector('dialog[open]') || root.contains(document.activeElement)) return;
    refreshSnapshot(location.href, undefined, true);
  }
  const liveTimer = setInterval(() => {
    if (!root.isConnected) { clearInterval(liveTimer); return; }
    refreshLiveList();
  }, 15000);
  document.addEventListener('visibilitychange', refreshLiveList);
  window.addEventListener('focus', refreshLiveList);
  window.addEventListener('popstate', () => {
    if (root.isConnected && !busy()) {
      [addDialog, editDialog, deleteDialog, viewDialog, historyDialog].filter(Boolean).forEach(dialog => { if (dialog.open) dialog.close(); });
      refreshSnapshot(location.href);
    }
  });
})();
;

/* Sales */
(() => {
  'use strict';
  const root = document.getElementById('accountsSalePage');
  const form = document.getElementById('accountsSaleForm');
  const button = document.getElementById('saleSaveButton');
  const feedback = document.getElementById('saleFeedback');
  const addDialog = document.getElementById('saleAddDialog');
  const paymentsDialog = document.getElementById('salePaymentsDialog');
  const paymentForm = document.getElementById('salePaymentForm');
  const paymentSaveButton = document.getElementById('salePaymentSaveButton');
  const viewDialog = document.getElementById('saleViewDialog');
  const editDialog = document.getElementById('saleEditDialog');
  const deleteDialog = document.getElementById('saleDeleteDialog');
  const editForm = document.getElementById('saleEditForm');
  const updateButton = document.getElementById('saleUpdateButton');
  const deleteButton = document.getElementById('saleDeleteButton');
  if (!root || !form || !button || !addDialog || !editDialog || !deleteDialog || !editForm || !updateButton || !deleteButton) return;
  let saving = false, loading = false, deleteUrl = '', opener = null;
  let scrollLocks = [];
  const busy = () => saving || loading;
  const csrf = () => form.elements.namedItem('csrfmiddlewaretoken').value;

  function notice(message, type = 'success') {
    if (typeof window.showToast === 'function') window.showToast(message, type);
    else if (feedback) {
      feedback.textContent = message; feedback.dataset.type = type; feedback.hidden = false;
    }
  }
  function clearErrors(targetForm, general) {
    general.hidden = true; general.textContent = '';
    const duplicateBox = targetForm.querySelector('.sale-duplicate-box');
    if (duplicateBox) duplicateBox.hidden = true;
    targetForm.querySelectorAll('[data-field-error]').forEach(node => { node.textContent = ''; });
    targetForm.querySelectorAll('[aria-invalid]').forEach(node => {
      node.removeAttribute('aria-invalid'); node.removeAttribute('aria-describedby');
    });
  }
  function showErrors(targetForm, general, errors) {
    let first;
    Object.entries(errors || {}).forEach(([name, values]) => {
      const text = values.map(value => value.message).join(' ');
      const target = [...targetForm.querySelectorAll('[data-field-error]')].find(node => node.dataset.fieldError === name);
      const field = targetForm.elements.namedItem(name);
      if (target && field) {
        target.textContent = text; field.setAttribute('aria-invalid', 'true');
        field.setAttribute('aria-describedby', target.id); first ||= field;
      } else { general.textContent += `${text} `; general.hidden = false; }
    });
    first?.focus();
  }
  async function requestJson(url, options = {}) {
    const response = await fetch(url, {credentials: 'same-origin', cache: 'no-store', ...options});
    if (!(response.headers.get('content-type') || '').includes('application/json')) {
      throw new Error('Unexpected response. Check your session and sale list before trying again.');
    }
    const data = await response.json();
    if (options.method === 'POST' && response.ok && data.ok) {
      document.dispatchEvent(new CustomEvent('accounts:notifications-refresh'));
    }
    return {response, data};
  }
  const postOptions = body => ({
    method: 'POST', headers: {'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': csrf()}, body
  });
  async function refreshSnapshot(url, historyMode, silent = false) {
    if (loading) return false;
    loading = true; root.setAttribute('aria-busy', 'true');
    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 15000);
      let response;
      try { response = await fetch(url, {credentials: 'same-origin', cache: 'no-store', signal: controller.signal}); }
      finally { clearTimeout(timeout); }
      if (!response.ok && response.status !== 400) throw new Error('Sale list could not be loaded.');
      const page = new DOMParser().parseFromString(await response.text(), 'text/html');
      const snapshot = page.getElementById('saleSnapshot');
      if (!snapshot) throw new Error('Sale list unavailable. Sign in again if your session has ended.');
      if (silent && (saving || document.hidden || document.querySelector('dialog[open]') || root.contains(document.activeElement))) return false;
      const current = document.getElementById('saleSnapshot');
      const positions = [...current.querySelectorAll('[class*=table-scroll]')].map(node => ({top: node.scrollTop, left: node.scrollLeft}));
      current.replaceWith(snapshot);
      snapshot.querySelectorAll('[class*=table-scroll]').forEach((node, index) => {
        if (positions[index]) {node.scrollTop = positions[index].top; node.scrollLeft = positions[index].left;}
      });
      if (historyMode === 'push') history.pushState(null, '', url);
      if (historyMode === 'replace') history.replaceState(null, '', url);
      window.lucide?.createIcons();
      return true;
    } catch (error) { if (!silent) notice(error.message, 'error'); return false; }
    finally { loading = false; root.removeAttribute('aria-busy'); }
  }
  function openPopup(dialog, trigger) {
    opener = trigger;
    scrollLocks = [...new Set([document.documentElement, document.body, ...document.querySelectorAll('.accounts-shell, .accounts-main')])]
      .map(node => ({node, value: node.style.getPropertyValue('overflow'), priority: node.style.getPropertyPriority('overflow')}));
    scrollLocks.forEach(({node}) => node.style.setProperty('overflow', 'hidden', 'important'));
    dialog.showModal(); window.lucide?.createIcons();
  }
  function restoreScroll() {
    scrollLocks.forEach(({node, value, priority}) => {
      if (value) node.style.setProperty('overflow', value, priority);
      else node.style.removeProperty('overflow');
    });
    scrollLocks = [];
    if (opener?.isConnected) opener.focus();
    else document.getElementById('saleSearch')?.focus();
    opener = null;
  }
  [addDialog, editDialog, deleteDialog, viewDialog, paymentsDialog].filter(Boolean).forEach(dialog => {
    dialog.addEventListener('close', restoreScroll);
    dialog.addEventListener('cancel', event => { if (saving) event.preventDefault(); });
    dialog.addEventListener('click', event => {
      if (saving) return;
      if (event.target.closest('[data-sale-close]')) dialog.close();
      else if (event.target === dialog) {
        const bounds = dialog.getBoundingClientRect();
        if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) dialog.close();
      }
    });
  });
  function setModalBusy(dialog, value) {
    dialog.querySelectorAll('button').forEach(node => { node.disabled = value; });
    dialog.setAttribute('aria-busy', String(value));
  }
  if (addDialog.dataset.formErrors === '1') openPopup(addDialog, document.getElementById('saleAddButton'));
  // Clone the validated Add fields once, with separate IDs for the edit popup.
  const fields = form.querySelector('.sale-form-grid').cloneNode(true);
  fields.querySelector('[name=received_amount]')?.closest('.sale-field')?.remove();
  fields.querySelectorAll('[id]').forEach(node => { node.id = `edit_${node.id}`; });
  fields.querySelectorAll('label[for]').forEach(node => { node.htmlFor = `edit_${node.htmlFor}`; });
  fields.querySelectorAll('[aria-describedby]').forEach(node => node.removeAttribute('aria-describedby'));
  document.getElementById('saleEditFields').replaceWith(fields);


  function showDuplicate(targetForm, data) {
    if (!data.duplicate) return false;
    const box = targetForm.querySelector('.sale-duplicate-box');
    box.querySelector('[data-sale-duplicate-message]').textContent = data.message;
    box.hidden = false;
    box.querySelector('[data-sale-duplicate-confirm]').focus();
    return true;
  }
  [form, editForm].forEach(targetForm => {
    targetForm.addEventListener('input', () => {
      targetForm.elements.namedItem('confirm_duplicate').value = '0';
      targetForm.querySelector('.sale-duplicate-box').hidden = true;
    });
    targetForm.addEventListener('click', event => {
      if (event.target.closest('[data-sale-duplicate-confirm]')) {
        targetForm.elements.namedItem('confirm_duplicate').value = '1';
        targetForm.requestSubmit();
      }
      if (event.target.closest('[data-sale-duplicate-cancel]')) {
        targetForm.querySelector('.sale-duplicate-box').hidden = true;
        targetForm.elements.namedItem('confirm_duplicate').value = '0';
        targetForm.elements.namedItem('invoice_number').focus();
      }
    });
  });

  form.addEventListener('submit', async event => {
    event.preventDefault(); if (busy()) return;
    saving = true; setModalBusy(addDialog, true);
    const general = document.getElementById('saleFormError'); clearErrors(form, general);
    const label = button.querySelector('span'); label.textContent = 'Saving…';
    try {
      const {response, data} = await requestJson((form.getAttribute('action') || location.href), postOptions(new FormData(form)));
      if (!response.ok || !data.ok) {
        if (showDuplicate(form, data)) return;
        showErrors(form, general, data.errors); notice(data.message || 'Sale could not be saved.', 'error'); return;
      }
      form.reset(); addDialog.close(); notice(data.message || 'Sale saved successfully.');
      if (!await refreshSnapshot(location.href, 'replace')) {
        notice('Sale was saved. Reload the list to see the new entry.', 'warning');
      }
    } catch (error) { notice(error.message || 'Unable to confirm the save. Check the list before submitting again.', 'error'); }
    finally { saving = false; setModalBusy(addDialog, false); label.textContent = 'Save Sale'; }
  });
  root.addEventListener('change', event => {
    if (event.target.id !== 'salePeriod') return;
    root.querySelectorAll('[data-sale-period]').forEach(node => {
      node.hidden = node.dataset.salePeriod !== event.target.value;
    });
  });
  root.addEventListener('submit', async event => {
    if (event.target.id !== 'saleSearchForm') return;
    event.preventDefault(); if (busy()) return;
    const url = new URL((event.target.getAttribute('action') || location.href), location.href);
    const filters = new FormData(event.target);
    for (const [name, value] of filters) url.searchParams.set(name, value);
    if (event.submitter?.name !== 'export') { refreshSnapshot(url, 'push'); return; }
    url.searchParams.set('export', 'xlsx');
    loading = true;
    const exportButton = event.submitter; exportButton.disabled = true;
    const exportLabel = exportButton.querySelector('span');
    if (exportLabel) exportLabel.textContent = 'Exporting…';
    root.setAttribute('aria-busy', 'true');
    try {
      const response = await fetch(url, {credentials: 'same-origin', cache: 'no-store'});
      if (!response.ok || !(response.headers.get('content-type') || '').includes('spreadsheetml')) {
        if (response.status === 400) {
          const errorPage = new DOMParser().parseFromString(await response.text(), 'text/html');
          const message = errorPage.querySelector('.sale-form-error')?.textContent.trim();
          throw new Error(message || 'Check the selected dates and try exporting again.');
        }
        throw new Error('Export could not be downloaded. Check your session and filters.');
      }
      const blobUrl = URL.createObjectURL(await response.blob());
      const link = document.createElement('a'); link.href = blobUrl;
      const filename = (response.headers.get('content-disposition') || '').match(/filename="([^"]+)"/);
      link.download = filename ? filename[1] : 'sale.xlsx';
      document.body.append(link); link.click(); link.remove();
      setTimeout(() => URL.revokeObjectURL(blobUrl), 10000);
      notice('Excel download started.');
    } catch (error) { notice(error.message, 'error'); }
    finally {
      loading = false; exportButton.disabled = false; root.removeAttribute('aria-busy');
      if (exportLabel) exportLabel.textContent = 'Export to Excel';
    }
  });
  root.addEventListener('click', async event => {
    const payments = event.target.closest('[data-sale-payments]');
    if (payments) {
      if (busy()) return;
      loading = true; payments.disabled = true;
      try {
        const {response, data} = await requestJson(payments.dataset.salePayments);
        if (!response.ok || !data.ok) throw new Error(data.message || 'Payments unavailable.');
        paymentForm.reset(); clearErrors(paymentForm, document.getElementById('salePaymentError'));
        paymentForm.action = payments.dataset.salePayments;
        paymentForm.elements.namedItem('request_token').value = crypto.randomUUID();
        paymentForm.elements.namedItem('date').value = data.today;
        paymentForm.elements.namedItem('date').min = data.sale_date;
        paymentForm.elements.namedItem('date').max = data.today;
        renderPayments(data);
        openPopup(paymentsDialog, payments);
      } catch (error) { notice(error.message, 'error'); }
      finally { loading = false; payments.disabled = false; }
      return;
    }

    const view = event.target.closest('[data-sale-view]');
    if (view) {
      if (busy() || !viewDialog) return;
      const details = view.closest('tr')?.querySelector('.sale-view-template');
      if (!details) { notice('Sale details are unavailable.', 'error'); return; }
      document.getElementById('saleViewContent').replaceChildren(details.content.cloneNode(true));
      openPopup(viewDialog, view);
      return;
    }
    const add = event.target.closest('#saleAddButton');
    if (add) { if (!busy()) openPopup(addDialog, add); return; }
    const link = event.target.closest('a[data-sale-page]');
    if (link) {
      if (event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
      event.preventDefault(); if (!busy()) refreshSnapshot(link.href, 'push'); return;
    }
    const edit = event.target.closest('[data-sale-edit]');
    const remove = event.target.closest('[data-sale-delete]');
    if ((!edit && !remove) || busy()) return;
    if (remove) {
      deleteUrl = remove.dataset.saleDelete;
      document.getElementById('saleDeleteCategory').textContent = remove.dataset.saleCategory || 'this entry';
      document.getElementById('saleDeleteError').hidden = true;
      openPopup(deleteDialog, remove); return;
    }
    loading = true; edit.disabled = true;
    try {
      const {response, data} = await requestJson(edit.dataset.saleEdit);
      if (!response.ok || !data.ok) { notice(data.message || 'Sale could not be opened.', 'error'); return; }
      editForm.reset(); clearErrors(editForm, document.getElementById('saleEditError'));
      editForm.action = edit.dataset.saleEdit;
      Object.entries(data.item).forEach(([name, value]) => {
        const field = editForm.elements.namedItem(name); if (field) field.value = value ?? '';
      });
      const invoiceBox = document.getElementById('saleCurrentInvoice');
      invoiceBox.hidden = !data.invoice_url;
      if (data.invoice_url) invoiceBox.querySelector('a').href = data.invoice_url;
      openPopup(editDialog, edit);
    } catch (error) { notice(error.message || 'Sale could not be opened.', 'error'); }
    finally { loading = false; edit.disabled = false; }
  });
  editForm.addEventListener('submit', async event => {
    event.preventDefault(); if (busy()) return;
    saving = true; setModalBusy(editDialog, true); updateButton.textContent = 'Saving…';
    const general = document.getElementById('saleEditError'); clearErrors(editForm, general);
    try {
      const {response, data} = await requestJson(editForm.action, postOptions(new FormData(editForm)));
      if (!response.ok || !data.ok) {
        if (showDuplicate(editForm, data)) return;
        showErrors(editForm, general, data.errors); general.textContent ||= data.message || 'Update failed.'; general.hidden = false; return;
      }
      editDialog.close(); notice(data.message || 'Sale updated successfully.');
      if (!await refreshSnapshot(location.href, 'replace')) notice('Sale updated. Reload the list to see the changes.', 'warning');
    } catch (_) {
      general.textContent = 'Unable to confirm the update. Close this popup and check the list before retrying.'; general.hidden = false;
    } finally { saving = false; setModalBusy(editDialog, false); updateButton.textContent = 'Save Changes'; }
  });
  deleteButton.addEventListener('click', async () => {
    if (busy() || !deleteUrl) return;
    saving = true; setModalBusy(deleteDialog, true); deleteButton.textContent = 'Deleting…';
    const general = document.getElementById('saleDeleteError'); general.hidden = true;
    try {
      const deleteData = new URLSearchParams();
      deleteData.set('csrfmiddlewaretoken', csrf());
      const {response, data} = await requestJson(deleteUrl, postOptions(deleteData));
      if (!response.ok || !data.ok) { general.textContent = data.message || 'Delete failed.'; general.hidden = false; return; }
      deleteDialog.close(); notice(data.message || 'Sale deleted successfully.'); deleteUrl = '';
      if (!await refreshSnapshot(location.href, 'replace')) notice('Sale deleted. Reload the list to see the changes.', 'warning');
    } catch (_) {
      general.textContent = 'Unable to confirm deletion. Close this popup and check the list before retrying.'; general.hidden = false;
    } finally { saving = false; setModalBusy(deleteDialog, false); deleteButton.textContent = 'Delete Sale'; }
  });

  function renderPayments(data) {
    document.getElementById('salePaymentSummary').textContent = `${data.customer} · Received ₹${data.received} · Balance ₹${data.balance}`;
    paymentForm.hidden = Number(data.balance) <= 0;
    paymentForm.elements.namedItem('amount').max = data.balance;
    const history = document.getElementById('salePaymentHistory'); history.replaceChildren();
    if (Number(data.opening_received) > 0) {
      const opening = document.createElement('p');
      opening.className = 'accounts-muted'; opening.textContent = `Previously received: ₹${data.opening_received}. Individual payment details were not recorded before this upgrade.`;
      history.append(opening);
    }
    data.items.forEach(item => {
      const card = document.createElement('article'); card.className = 'sale-payment-card';
      const heading = document.createElement('strong'); heading.textContent = `₹${item.amount} · ${item.date}`;
      const detail = document.createElement('p'); detail.textContent = `${item.method} · ${item.reference || 'No reference'} · ${item.actor}`;
      const note = document.createElement('p'); note.textContent = item.note;
      card.append(heading, detail, note); history.append(card);
    });
    if (!history.children.length) history.textContent = 'No payments recorded yet.';
  }
  paymentForm.addEventListener('submit', async event => {
    event.preventDefault(); if (busy()) return;
    saving = true; setModalBusy(paymentsDialog, true);
    const general = document.getElementById('salePaymentError'); clearErrors(paymentForm, general);
    paymentSaveButton.textContent = 'Recording…';
    try {
      const {response, data} = await requestJson(paymentForm.action, postOptions(new FormData(paymentForm)));
      if (!response.ok || !data.ok) {
        showErrors(paymentForm, general, data.errors);
        general.textContent ||= data.message || 'Payment could not be recorded.'; general.hidden = false; return;
      }
      notice(data.message); paymentsDialog.close();
      if (!await refreshSnapshot(location.href, 'replace')) notice('Payment recorded. Reload the list to see updated totals.', 'warning');
    } catch (_) {
      general.textContent = 'Unable to confirm payment. Retry without changing the form, or close and check Payment History first.'; general.hidden = false;
    } finally { saving = false; setModalBusy(paymentsDialog, false); paymentSaveButton.textContent = 'Record Payment'; }
  });
  function refreshLiveList() {
    if (!root.isConnected || document.hidden || busy() || document.querySelector('dialog[open]') || root.contains(document.activeElement)) return;
    refreshSnapshot(location.href, undefined, true);
  }
  const liveTimer = setInterval(() => {
    if (!root.isConnected) { clearInterval(liveTimer); return; }
    refreshLiveList();
  }, 15000);
  document.addEventListener('visibilitychange', refreshLiveList);
  window.addEventListener('focus', refreshLiveList);
  window.addEventListener('popstate', () => {
    if (root.isConnected && !busy()) {
      [addDialog, editDialog, deleteDialog, viewDialog, paymentsDialog].filter(Boolean).forEach(dialog => { if (dialog.open) dialog.close(); });
      refreshSnapshot(location.href);
    }
  });
})();
;

/* Accounts Dashboard */
(() => {
  'use strict';
  const root = document.getElementById('accountsDashboardPage');
  const form = document.getElementById('dashboardFilterForm');
  if (!root || !form) return;
  const status = document.getElementById('dashboardLiveStatus');
  const period = document.getElementById('dashboardPeriod');
  const defaults = Object.fromEntries(new FormData(form));
  let pending = null, sequence = 0, busy = false;
  function toggleFields() {
    root.querySelectorAll('[data-dashboard-period]').forEach(wrapper => {
      const active = wrapper.dataset.dashboardPeriod === period.value;
      wrapper.hidden = !active;
      wrapper.querySelectorAll('input').forEach(input => { input.disabled = !active; });
    });
  }
  function syncFilters(url) {
    const params = new URL(url, location.href).searchParams;
    for (const name of ['period', 'month', 'date', 'start', 'end']) {
      const field = form.elements.namedItem(name);
      if (field) field.value = params.get(name) ?? (name === 'period' ? 'monthly' : defaults[name] || '');
    }
    toggleFields();
  }
  async function update(url, historyMode = '', automatic = false) {
    if (!root.isConnected || (automatic && busy)) return;
    pending?.abort(); pending = new AbortController();
    const controller = pending, requestNumber = ++sequence;
    busy = true; root.setAttribute('aria-busy', 'true');
    if (!automatic) status.textContent = 'Updating…';
    const timeout = setTimeout(() => controller.abort(), 15000);
    try {
      const response = await fetch(url, {credentials:'same-origin', cache:'no-store', signal:controller.signal});
      if (!response.ok && response.status !== 400) throw new Error('Dashboard unavailable. Check your login and try Update Now.');
      const page = new DOMParser().parseFromString(await response.text(), 'text/html');
      const incoming = page.getElementById('dashboardSnapshot');
      if (!incoming) throw new Error('Your session may have ended. Please sign in again.');
      if (requestNumber !== sequence) return;
      const old = document.getElementById('dashboardSnapshot');
      const scrolls = [...old.querySelectorAll('.dashboard-table-scroll')].map(node => [node.scrollTop,node.scrollLeft]);
      old.replaceWith(incoming);
      incoming.querySelectorAll('.dashboard-table-scroll').forEach((node,index) => {
        if (scrolls[index]) [node.scrollTop,node.scrollLeft] = scrolls[index];
      });
      if (historyMode === 'push') history.pushState(null, '', url);
      if (historyMode === 'replace') history.replaceState(null, '', url);
      window.lucide?.createIcons();
      status.textContent = incoming.dataset.filterValid === '1'
        ? `Updated ${new Date().toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'})} · Every 30 seconds`
        : 'Check the selected dates';
      status.classList.toggle('is-error', incoming.dataset.filterValid !== '1');
    } catch (error) {
      if (requestNumber !== sequence) return;
      status.textContent = error.name === 'AbortError' ? 'Update timed out. Try Update Now.' : error.message;
      status.classList.add('is-error');
    } finally {
      clearTimeout(timeout);
      if (requestNumber === sequence) {busy = false;root.removeAttribute('aria-busy');pending = null;}
    }
  }
  period.addEventListener('change', toggleFields);
  form.addEventListener('submit', event => {
    event.preventDefault();
    const url = new URL((form.getAttribute('action') || location.href), location.href);
    for (const [name,value] of new FormData(form)) url.searchParams.set(name,value);
    update(url, 'push');
  });
  document.getElementById('dashboardRefresh').addEventListener('click', () => update(location.href));
  document.getElementById('dashboardReset').addEventListener('click', event => {
    if (event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    event.preventDefault();syncFilters(event.currentTarget.href);update(event.currentTarget.href, 'push');
  });
  window.addEventListener('popstate', () => {
    if (!root.isConnected) return;
    syncFilters(location.href);update(location.href);
  });
  const timer = setInterval(() => {
    if (!root.isConnected) {clearInterval(timer);pending?.abort();return;}
    if (!document.hidden && document.getElementById('dashboardSnapshot').dataset.filterValid === '1') update(location.href, '', true);
  }, 30000);
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden && root.isConnected && document.getElementById('dashboardSnapshot').dataset.filterValid === '1') update(location.href, '', true);
  });
  toggleFields();
})();

/* Shared calendar */
(() => {
  'use strict';
  const months = ['January','February','March','April','May','June','July','August','September','October','November','December'];
  let input = null, trigger = null, year = 0, month = 0, mode = 'date', number = 0;
  const popup = document.createElement('div');
  popup.id = 'accountsCalendarPopover'; popup.className = 'accounts-calendar';
  popup.setAttribute('role', 'dialog'); popup.setAttribute('aria-label', 'Choose date or month');
  const nativePopover = typeof popup.showPopover === 'function';
  if (nativePopover) popup.setAttribute('popover', 'auto'); else popup.hidden = true;
  document.body.append(popup);
  const pad = value => String(value).padStart(2, '0');
  const localDate = (y, m, d) => { const value = new Date(0); value.setFullYear(y, m, d); value.setHours(12,0,0,0); return value; };
  const dateString = value => `${String(value.getFullYear()).padStart(4,'0')}-${pad(value.getMonth()+1)}-${pad(value.getDate())}`;
  const isOpen = () => nativePopover ? popup.matches(':popover-open') : !popup.hidden;
  function release() {
    if (trigger) trigger.setAttribute('aria-expanded', 'false');
    input = null; trigger = null;
  }
  function close(focus = false) {
    const previous = trigger;
    if (nativePopover && isOpen()) popup.hidePopover(); else popup.hidden = true;
    release(); if (focus && previous?.isConnected) previous.focus();
  }
  popup.addEventListener('toggle', event => { if (event.newState === 'closed' && !isOpen()) release(); });
  function position() {
    if (!trigger) return;
    const control = trigger.closest('.accounts-calendar-control');
    const rect = control.getBoundingClientRect();
    const width = popup.offsetWidth, height = popup.offsetHeight;
    const left = Math.max(12, Math.min(rect.left, window.innerWidth-width-12));
    let top = rect.bottom + 8;
    if (top + height > window.innerHeight - 12) top = Math.max(12, rect.top-height-8);
    popup.style.left = `${left}px`; popup.style.top = `${top}px`;
  }
  function render() {
    if (!input) return;
    const monthMode = mode === 'month';
    let content = `<div class="accounts-calendar-head"><button type="button" class="accounts-calendar-nav" data-nav="-1" aria-label="Previous ${monthMode?'year':'month'}">‹</button><button type="button" class="accounts-calendar-title" data-title>${monthMode ? year : `${months[month]} ${year}`}</button><button type="button" class="accounts-calendar-nav" data-nav="1" aria-label="Next ${monthMode?'year':'month'}">›</button></div>`;
    if (monthMode) {
      content += '<div class="accounts-calendar-months">';
      months.forEach((label, index) => {
        const selected = input.value.startsWith(`${String(year).padStart(4,'0')}-${pad(index+1)}`);
        content += `<button type="button" class="accounts-calendar-month${selected?' selected':''}" data-month="${index}" aria-pressed="${selected}">${label.slice(0,3)}</button>`;
      });
      content += '</div>';
    } else {
      content += '<div class="accounts-calendar-weekdays" aria-hidden="true">'+['SU','MO','TU','WE','TH','FR','SA'].map(day=>`<span>${day}</span>`).join('')+'</div><div class="accounts-calendar-days">';
      const first = localDate(year,month,1).getDay();
      const length = localDate(year,month+1,0).getDate();
      for (let blank=0;blank<first;blank++) content += '<span></span>';
      const today = dateString(new Date());
      for (let day=1;day<=length;day++) {
        const value = dateString(localDate(year,month,day));
        const selected = input.value === value;
        content += `<button type="button" class="accounts-calendar-day${selected?' selected':''}${today===value?' today':''}" data-day="${day}" aria-label="${day} ${months[month]} ${year}" aria-pressed="${selected}">${day}</button>`;
      }
      content += '</div>';
    }
    content += `<div class="accounts-calendar-footer"><button type="button" data-clear>Clear</button><button type="button" data-today>${input.dataset.calendarKind==='month'?'This month':'Today'}</button></div>`;
    popup.innerHTML = content; position();
  }
  function choose(value) {
    const target = input;
    target.value = value;
    target.dispatchEvent(new Event('input', {bubbles:true}));
    target.dispatchEvent(new Event('change', {bubbles:true}));
    close(true);
  }
  function open(target, button) {
    if (isOpen() && input === target) { close(true); return; }
    close(); input = target; trigger = button;
    const parsed = /^(\d{4})-(\d{2})/.exec(target.value);
    const now = new Date();
    year = parsed ? Number(parsed[1]) : now.getFullYear();
    month = parsed ? Number(parsed[2])-1 : now.getMonth();
    if (year < 1 || year > 9998 || month < 0 || month > 11) { year=now.getFullYear(); month=now.getMonth(); }
    mode = target.dataset.calendarKind;
    popup.hidden = false;
    const owner = target.closest('dialog');
    (owner || document.body).append(popup);
    trigger.setAttribute('aria-expanded','true');
    render();
    if (nativePopover) popup.showPopover();
    position();
    (popup.querySelector('.selected') || popup.querySelector('[data-today]'))?.focus();
  }
  popup.addEventListener('click', event => {
    const button = event.target.closest('button'); if (!button || !input) return;
    if (button.hasAttribute('data-nav')) {
      const direction = Number(button.dataset.nav);
      if (mode === 'month') year = Math.min(9998,Math.max(1,year+direction));
      else { const value=localDate(year,month+direction,1); if(value.getFullYear()>=1&&value.getFullYear()<=9998){year=value.getFullYear();month=value.getMonth();} }
      render(); popup.querySelector(`[data-nav="${direction}"]`)?.focus();
    } else if (button.hasAttribute('data-title')) {
      if (input.dataset.calendarKind === 'date') { mode=mode==='month'?'date':'month'; render(); popup.querySelector('[data-title]')?.focus(); }
    } else if (button.hasAttribute('data-month')) {
      month=Number(button.dataset.month);
      if(input.dataset.calendarKind==='month') choose(`${String(year).padStart(4,'0')}-${pad(month+1)}`);
      else { mode='date'; render(); popup.querySelector('[data-day="1"]')?.focus(); }
    } else if (button.hasAttribute('data-day')) choose(dateString(localDate(year,month,Number(button.dataset.day))));
    else if (button.hasAttribute('data-clear')) choose('');
    else if (button.hasAttribute('data-today')) choose(input.dataset.calendarKind==='month'?dateString(new Date()).slice(0,7):dateString(new Date()));
  });
  function initialise() {
    document.querySelectorAll('.accounts-workspace input[type="date"], .accounts-workspace input[type="month"]').forEach(field => {
      if(field.dataset.calendarKind) return;
      field.dataset.calendarKind=field.type;
      field.type='text'; field.readOnly=true;
      field.placeholder=field.dataset.calendarKind==='month'?'Choose month':'Choose date';
      const wrapper=document.createElement('div'); wrapper.className='accounts-calendar-control';
      field.before(wrapper); wrapper.append(field);
      const button=document.createElement('button');button.type='button';button.className='accounts-calendar-toggle';
      button.id=`accountsCalendarButton${++number}`;button.setAttribute('aria-label',`Choose ${field.dataset.calendarKind}`);
      button.setAttribute('aria-haspopup','dialog');button.setAttribute('aria-expanded','false');button.setAttribute('aria-controls',popup.id);
      button.innerHTML='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="3"/><path d="M16 3v4M8 3v4M3 11h18"/></svg>';
      wrapper.append(button);
      button.addEventListener('click',()=>open(field,button));
      field.addEventListener('click',()=>open(field,button));
      field.addEventListener('keydown',event=>{if(['Enter',' ','ArrowDown'].includes(event.key)){event.preventDefault();open(field,button);}});
    });
  }
  document.addEventListener('keydown',event=>{
    if(event.key==='Escape'&&isOpen()){event.preventDefault();event.stopPropagation();close(true);}
  },true);
  if(!nativePopover) document.addEventListener('pointerdown',event=>{
    if(isOpen()&&!popup.contains(event.target)&&!trigger?.closest('.accounts-calendar-control').contains(event.target)) close();
  });
  window.addEventListener('resize',()=>{if(isOpen())position();});
  document.addEventListener('scroll',()=>{if(isOpen())close();},true);
  document.querySelectorAll('.accounts-workspace dialog').forEach(dialog => dialog.addEventListener('close',()=>{if(input?.closest('dialog')===dialog)close();}));
  initialise();
  new MutationObserver(()=>{if(input&&!input.isConnected)close();initialise();}).observe(document.body,{childList:true,subtree:true});
})();
;


/* Accounts notifications: Team Lead table style */
(() => {
  function initAccountsNotifications() {
    const root = document.getElementById('accountsNotificationsPage');
    if (!root || root.dataset.initialized === '1') return;
    root.dataset.initialized = '1';
    const form = document.getElementById('notificationFilterForm');
    const filter = document.getElementById('notificationFilter');
    const kind = document.getElementById('notificationKind');
    const search = document.getElementById('notificationSearch');
    const dropdown = document.getElementById('notificationCategoryDropdown');
    const label = document.getElementById('notificationCategoryLabel');
    const readAll = document.getElementById('notificationReadAll');
    const status = document.getElementById('notificationLiveStatus');
    const scroll = document.getElementById('notificationScroll');
    const csrf = root.querySelector('[name=csrfmiddlewaretoken]').value;
    const ids = ['notificationList', 'notificationPagination', 'notificationUnreadCount', 'notificationTotalCount', 'notificationTabUnread', 'notificationArchivedCount', 'notificationResultCount'];
    let currentUrl = new URL(root.dataset.feedUrl, location.origin);
    currentUrl.search = location.search;
    let controller, sequence = 0, saving = false, loading = false, debounce;
    function publishCount(count) {
      document.dispatchEvent(new CustomEvent('accounts:notification-count', {detail: {count: Number(count) || 0}}));
    }
    function toast(message, type = 'success') {
      status.textContent = message;
      if (typeof window.showToast === 'function') window.showToast(message, type);
    }
    function syncControls() {
      root.querySelectorAll('[data-folder]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.folder === filter.value)));
      dropdown.querySelectorAll('[data-kind]').forEach(button => {
        const selected = button.dataset.kind === kind.value;
        button.classList.toggle('selected', selected);
        if (selected) label.textContent = button.textContent;
      });
    }
    async function refresh(url = currentUrl, silent = false) {
      if (saving || !root.isConnected) return;
      if (silent && loading) return;
      controller?.abort();
      const mySequence = ++sequence;
      const taskController = new AbortController();
      controller = taskController;
      loading = true;
      const timeout = setTimeout(() => taskController.abort(), 15000);
      if (!silent) status.textContent = 'Loading notifications…';
      try {
        const response = await fetch(url, {credentials:'same-origin', cache:'no-store', headers:{'X-Requested-With':'XMLHttpRequest'}, signal:taskController.signal});
        if (!response.ok || response.redirected) throw new Error('Could not load notifications. Please check your login.');
        const doc = new DOMParser().parseFromString(await response.text(), 'text/html');
        if (mySequence !== sequence || !root.isConnected) return;
        if (!doc.getElementById('accountsNotificationsPage') || ids.some(id => !doc.getElementById(id))) throw new Error('Notification page could not be updated.');
        const top = scroll.scrollTop, left = scroll.scrollLeft;
        ids.forEach(id => document.getElementById(id).replaceChildren(...doc.getElementById(id).childNodes));
        currentUrl = new URL(url, location.origin);
        history.replaceState(null, '', currentUrl.pathname + currentUrl.search);
        filter.value = doc.getElementById('notificationFilter').value;
        syncControls();
        const count = Number(document.getElementById('notificationUnreadCount').textContent);
        readAll.disabled = count === 0;
        publishCount(count);
        scroll.scrollTop = top; scroll.scrollLeft = left;
        if (window.lucide) window.lucide.createIcons();
        status.textContent = 'Updated just now · checks every 15 seconds';
        return true;
      } catch (error) {
        if (mySequence !== sequence) return;
        status.textContent = error.name === 'AbortError' ? 'Connection timed out. Updates will retry.' : error.message;
        if (!silent) toast(status.textContent, 'error');
      } finally {
        clearTimeout(timeout);
        if (mySequence === sequence) loading = false;
      }
    }
    async function applyFilters() {
      clearTimeout(debounce); debounce = null;
      const url = new URL(root.dataset.feedUrl, location.origin);
      url.search = new URLSearchParams(new FormData(form)).toString();
      if (await refresh(url)) scroll.scrollTop = 0;
    }
    async function performAction(url, action, button) {
      if (saving) return;
      clearTimeout(debounce); debounce = null;
      controller?.abort(); sequence++; loading = false;
      saving = true; button.disabled = true; root.setAttribute('aria-busy','true');
      try {
        const response = await fetch(url, {method:'POST', credentials:'same-origin', headers:{'X-CSRFToken':csrf, 'X-Requested-With':'XMLHttpRequest', 'Content-Type':'application/x-www-form-urlencoded'}, body:new URLSearchParams({action})});
        if (response.redirected) throw new Error('Please log in again.');
        const data = await response.json();
        if (!response.ok || !data.ok) throw new Error(data.message || 'Operation failed.');
        document.getElementById('notificationUnreadCount').textContent = data.unread_count;
        publishCount(data.unread_count);
        toast(data.message);
        if (action === 'open' && data.url) {
          const destination = new URL(data.url, location.origin);
          if (destination.origin !== location.origin) throw new Error('Invalid destination.');
          location.assign(destination.href); return;
        }
        saving = false;
        // Preserve the latest search/category/folder after an action.
        const refreshUrl = new URL(root.dataset.feedUrl, location.origin);

refreshUrl.search = new URLSearchParams(
  new FormData(form)
).toString();

if (currentUrl.searchParams.has('page')) {
  refreshUrl.searchParams.set(
    'page',
    currentUrl.searchParams.get('page')
  );
}

await refresh(refreshUrl, true);
      } catch (error) {
        toast(error instanceof SyntaxError ? 'Unexpected response. Please try again.' : error.message, 'error');
      } finally {
        saving = false; root.removeAttribute('aria-busy');
        if (button.isConnected) button.disabled = false;
        readAll.disabled = Number(document.getElementById('notificationUnreadCount').textContent) === 0;
      }
    }
    form.addEventListener('submit', event => {event.preventDefault(); applyFilters();});
    search.addEventListener('input', () => {clearTimeout(debounce); debounce = setTimeout(applyFilters, 350);});
    readAll.addEventListener('click', () => performAction(root.dataset.readAllUrl, 'read_all', readAll));
    root.addEventListener('click', async event => {
      const action = event.target.closest('[data-notification-action]');
      if (action) {const row=action.closest('[data-action-url]'); if(row) performAction(row.dataset.actionUrl,action.dataset.notificationAction,action); return;}
      const tab=event.target.closest('[data-folder]');
      if(tab){filter.value=tab.dataset.folder; syncControls(); applyFilters(); return;}
      const category=event.target.closest('[data-kind]');
      if(category){kind.value=category.dataset.kind; syncControls(); dropdown.open=false; dropdown.querySelector('summary').focus(); applyFilters(); return;}
      const link=event.target.closest('#notificationPagination a');
      if(link && !event.ctrlKey && !event.metaKey && !event.shiftKey && !event.altKey){event.preventDefault(); if(await refresh(new URL(link.href))) scroll.scrollTop=0;}
    });
    document.addEventListener('click', event => {if(!dropdown.contains(event.target)) dropdown.open=false;});
    dropdown.addEventListener('keydown', event => {if(event.key==='Escape'){dropdown.open=false; dropdown.querySelector('summary').focus();}});
    const timer=setInterval(() => {
      if(!root.isConnected){clearInterval(timer); controller?.abort(); return;}
      if(!document.hidden && !scroll.contains(document.activeElement) && !debounce) refresh(currentUrl,true);
    },15000);
    document.addEventListener('visibilitychange', () => {if(!document.hidden && root.isConnected) refresh(currentUrl,true);});
    syncControls(); publishCount(document.getElementById('notificationUnreadCount').textContent);
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',initAccountsNotifications,{once:true});
  else initAccountsNotifications();
})();

/* Live Accounts sidebar notification badge */
(() => {
  function initAccountsNotificationBadge() {
    const link = document.getElementById("accountsNotificationLink");
    const badge = document.getElementById("accountsNotificationBadge");

    if (!link || !badge || link.dataset.badgeReady === "1") return;
    link.dataset.badgeReady = "1";

    let busy = false;
    let revision = 0;
    let refreshPending = false;

    function updateBadge(value) {
      const count = Math.max(0, Number(value) || 0);

      badge.hidden = count === 0;
      badge.textContent = count > 99 ? "99+" : String(count);

      link.setAttribute(
        "aria-label",
        count
          ? `Notifications, ${count} unread`
          : "Notifications, no unread notifications"
      );
    }

    document.addEventListener("accounts:notification-count", (event) => {
      revision += 1;
      updateBadge(event.detail.count);
    });

    async function refreshBadge() {
      if (document.hidden || !link.isConnected) return;
      if (busy) { refreshPending = true; return; }

      busy = true;
      const startedRevision = revision;
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 10000);

      try {
        const response = await fetch(link.dataset.feedUrl, {
          credentials: "same-origin",
          cache: "no-store",
          headers: {
            "X-Requested-With": "XMLHttpRequest",
          },
          signal: controller.signal,
        });

        if (!response.ok || response.redirected) return;

        const data = await response.json();

        // Keep a newer count received after a read/archive action.
        if (data.ok && revision === startedRevision) {
          updateBadge(data.unread_count);
        }
      } catch {
        // Keep the previous count during temporary connection failures.
      } finally {
        clearTimeout(timeout);
        busy = false;
        if (refreshPending) {refreshPending = false; refreshBadge();}
      }
    }

    document.addEventListener("accounts:notifications-refresh", refreshBadge);
    refreshBadge();

    const timer = setInterval(() => {
      if (!link.isConnected) {
        clearInterval(timer);
        return;
      }
      refreshBadge();
    }, 15000);

    document.addEventListener("visibilitychange", () => {
      if (!document.hidden) refreshBadge();
    });

    window.addEventListener("focus", refreshBadge);
  }

  if (document.readyState === "loading") {
    document.addEventListener(
      "DOMContentLoaded",
      initAccountsNotificationBadge,
      { once: true }
    );
  } else {
    initAccountsNotificationBadge();
  }
})();