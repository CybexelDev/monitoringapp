/* Master Admin read receipts. Shared chat permissions stay on the server. */
(() => {
  'use strict';
  const root = document.getElementById('memberChatPage');
  if (!root || !root.dataset.metaUrl || !root.dataset.readUrl) return;
  window.disposeMasterChatReceipts?.();
  const mode = root.dataset.mode;
  const targetId = root.dataset.socketPath?.match(/\/(\d+)\/$/)?.[1];
  const messages = root.querySelector(mode === 'group' ? '#chat-area' : '#chat-messages');
  let receipts = new Map(), acknowledged = 0;
  let loading = false, reading = false, again = false, paused = false, disposed = false, denied = false;
  let socket, retry, refreshTimer, readTimer;
  let socketDenied = false;
  window.masterChatReceiptStatus = {loaded: true, metadata: null, read: null, socket: null};
  const requests = new Set(), listeners = [];
  const listen = (node, name, fn) => {
    node?.addEventListener(name, fn);
    if (node) listeners.push(() => node.removeEventListener(name, fn));
  };
  const active = () => !disposed && !paused && !denied && root.isConnected && !document.hidden;

  async function request(url, options = {}) {
    const controller = new AbortController();
    requests.add(controller);
    const timeout = setTimeout(() => controller.abort(), 12000);
    try {
      const response = await fetch(url, {...options, credentials: 'same-origin', cache: 'no-store', signal: controller.signal});
      window.masterChatReceiptStatus[options.method === 'POST' ? 'read' : 'metadata'] = response.status;
      if ([401, 403].includes(response.status)) {
        denied = true;
        socket?.close();
      }
      if (!response.ok || response.redirected) throw new Error('Chat session unavailable');
      const data = await response.json();
      if (data.ok !== true) throw new Error('Chat metadata unavailable');
      return data;
    } finally {
      clearTimeout(timeout);
      requests.delete(controller);
    }
  }

  function setBadge(link, value) {
    const number = Number(value);
    const count = Number.isSafeInteger(number) && number > 0 ? number : 0;
    let badge = link.querySelector('.member-unread-badge');
    if (!badge) {
      badge = document.createElement('span');
      badge.className = 'member-unread-badge';
      link.append(badge);
    }
    badge.hidden = count === 0;
    const label = count > 99 ? '99+' : String(count);
    if (badge.textContent !== label) badge.textContent = label;
    badge.title = `${count} unread messages`;
    badge.setAttribute('aria-label', badge.title);
  }

  function decorateTicks() {
    messages?.querySelectorAll('.message-row.sent[data-message-id]').forEach(row => {
      let tick = row.querySelector('.member-read-tick');
      if (['true', '1'].includes(row.dataset.deleted)) { tick?.remove(); return; }
      const time = row.querySelector('.message-time');
      if (!time) return;
      if (!tick) {
        tick = document.createElement('span');
        tick.className = 'member-read-tick';
        time.append(tick);
      }
      const state = receipts.get(String(row.dataset.messageId));
      const seen = state?.seen === true;
      const text = seen ? '✓✓' : '✓';
      if (tick.textContent !== text) tick.textContent = text;
      tick.classList.toggle('seen', seen);
      tick.title = mode === 'group' && state
        ? `Read by ${state.read_count} of ${state.reader_count} members${seen ? ' · Seen by all' : ''}`
        : seen ? 'Seen' : 'Sent · not seen yet';
      tick.setAttribute('aria-label', tick.title);
    });
  }

  function queueRefresh() {
    if (!active()) return;
    clearTimeout(refreshTimer);
    refreshTimer = setTimeout(refresh, 100);
  }

  async function refresh() {
    if (!active()) return;
    if (loading) { again = true; return; }
    loading = true;
    try {
      const url = new URL(root.dataset.metaUrl, location.href);
      if (targetId) { url.searchParams.set('kind', mode); url.searchParams.set('target_id', targetId); }
      const data = await request(url);
      if (!active()) return;
      if (![data.personal, data.groups, data.receipts].every(Array.isArray)) throw new Error('Invalid chat metadata');
      const peers = new Map(data.personal.map(item => [String(item.peer_id), item.unread]));
      const groups = new Map(data.groups.map(item => [String(item.group_id), item.unread]));
      root.querySelectorAll('.chat-user-row[data-peer-id]').forEach(link => setBadge(link, peers.get(link.dataset.peerId)));
      root.querySelectorAll('.chat-group-row[data-group-id]').forEach(link => setBadge(link, groups.get(link.dataset.groupId)));
      receipts = new Map(data.receipts.map(item => [String(item.message_id), item]));
      decorateTicks();
      queueRead();
    } catch (error) {
      if (error.name !== 'AbortError') console.warn('Master chat metadata unavailable; inspect the metadata request status.', window.masterChatReceiptStatus.metadata);
    } finally {
      loading = false;
      if (again) { again = false; queueRefresh(); }
    }
  }

  function queueRead() {
    clearTimeout(readTimer);
    if (active()) readTimer = setTimeout(markRead, 180);
  }

  async function markRead() {
    if (!active() || reading || !messages || !targetId || !document.hasFocus()) return;
    if (!messages.getClientRects().length || messages.scrollHeight - messages.scrollTop - messages.clientHeight >= 90) return;
    if (root.querySelector('#memberMessageSearch')?.value.trim()) return;
    const ids = [...messages.querySelectorAll('.message-row[data-message-id]')]
      .filter(row => !row.hidden).map(row => Number(row.dataset.messageId))
      .filter(id => Number.isSafeInteger(id) && id > 0);
    const latest = ids.reduce((max, id) => Math.max(max, id), 0);
    if (!latest || latest <= acknowledged) return;
    const token = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    if (!token) return;
    reading = true;
    try {
      const data = await request(root.dataset.readUrl, {
        method: 'POST', headers: {'X-CSRFToken': token},
        body: new URLSearchParams({kind: mode, target_id: targetId, message_id: String(latest)})
      });
      const id = Number(data.last_read_id);
      if (Number.isSafeInteger(id)) acknowledged = Math.max(acknowledged, id);
      queueRefresh();
    } catch (error) {
      if (error.name !== 'AbortError') console.warn('Master chat read receipt not saved; inspect the read request status.', window.masterChatReceiptStatus.read);
    }
    finally { reading = false; }
  }

  function connect() {
    if (!active() || socketDenied || socket?.readyState === 0 || socket?.readyState === 1) return;
    clearTimeout(retry);
    try {
      const url = new URL(root.dataset.updatesPath || '/ws/master/chat-updates/', location.href);
      url.protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
      socket = new WebSocket(url);
      socket.onopen = () => { window.masterChatReceiptStatus.socket = 'connected'; queueRefresh(); };
      socket.onmessage = event => {
        try { if (JSON.parse(event.data).action === 'sync_chat_meta') queueRefresh(); } catch (_) {}
      };
      socket.onclose = event => {
        window.masterChatReceiptStatus.socket = event.code;
        // A receipt socket failure must not disable valid HTTP metadata/read APIs.
        if (event.code === 4403 || event.code === 4401) socketDenied = true;
        queueRefresh();
        if (active() && !socketDenied) retry = setTimeout(connect, 3000);
      };
    } catch (_) { if (active()) retry = setTimeout(connect, 3000); }
  }

  const observer = new MutationObserver(changes => {
    const relevant = changes.some(change => {
      if (change.target.closest?.('.member-read-tick')) return false;
      if (change.type === 'attributes') return true;
      return [...change.addedNodes, ...change.removedNodes].some(node => node.nodeType === 1 &&
        (node.matches?.('.message-row,.message-time') || node.querySelector?.('.message-row')));
    });
    if (relevant) { decorateTicks(); queueRefresh(); queueRead(); }
  });
  if (messages) observer.observe(messages, {childList: true, subtree: true, attributes: true, attributeFilter: ['data-deleted', 'data-message-id']});
  const resume = () => { if (active()) { decorateTicks(); connect(); queueRefresh(); queueRead(); } };
  listen(messages, 'scroll', queueRead);
  listen(window, 'focus', resume);
  listen(window, 'online', resume);
  listen(document, 'visibilitychange', () => {
    if (document.hidden) { clearTimeout(refreshTimer); clearTimeout(readTimer); requests.forEach(controller => controller.abort()); }
    else resume();
  });
  listen(document, 'admin-chat-contacts-updated', queueRefresh);
  listen(document, 'master-chat-messages-updated', () => { decorateTicks(); queueRefresh(); queueRead(); });
  listen(root.querySelector('#memberMessageSearch'), 'input', queueRead);
  listen(window, 'pagehide', () => {
    paused = true; clearTimeout(retry); clearTimeout(refreshTimer); clearTimeout(readTimer);
    requests.forEach(controller => controller.abort()); socket?.close(); socket = null;
  });
  listen(window, 'pageshow', () => { paused = false; resume(); });
  const poll = setInterval(() => {
    if (!root.isConnected) { window.disposeMasterChatReceipts?.(); return; }
    resume();
  }, 15000);
  window.disposeMasterChatReceipts = () => {
    disposed = true; clearInterval(poll); clearTimeout(retry); clearTimeout(refreshTimer); clearTimeout(readTimer);
    observer.disconnect(); listeners.forEach(remove => remove());
    requests.forEach(controller => controller.abort()); socket?.close();
  };
  window.masterChatReceiptStatus.refresh = () => { denied = false; socketDenied = false; resume(); };
  decorateTicks(); refresh(); connect();
})();
