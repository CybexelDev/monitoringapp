(() => {
  'use strict';

  window.disposeMemberChatReceipts?.();

  const root = document.getElementById('memberChatPage');
  if (!root) return;

  const metaUrl = root.dataset.metaUrl;
  const readUrl = root.dataset.readUrl;
  if (!metaUrl || !readUrl) return;

  const mode = root.dataset.mode;
  const targetId = (root.dataset.socketPath || '')
    .match(/\/(\d+)\/$/)?.[1];

  const messages = root.querySelector(
    mode === 'group' ? '#chat-area' : '#chat-messages'
  );

  let stopped = false;
  let socket, retry, refreshTimer, readTimer, polling;
  let loading = false;
  let again = false;
  let reading = false;
  let acknowledged = 0;
  let receipts = new Map();

  const controllers = new Set();
  const listeners = [];

  function listen(node, event, handler) {
    if (!node) return;

    node.addEventListener(event, handler);
    listeners.push(() => node.removeEventListener(event, handler));
  }

  async function request(url, options = {}) {
    const controller = new AbortController();
    controllers.add(controller);

    try {
      const response = await fetch(url, {
        ...options,
        credentials: 'same-origin',
        cache: 'no-store',
        signal: controller.signal
      });

      if (!response.ok) {
        throw new Error(`Chat metadata HTTP ${response.status}`);
      }

      const data = await response.json();

      if (!data.ok) {
        throw new Error('Chat metadata unavailable');
      }

      return data;
    } finally {
      controllers.delete(controller);
    }
  }

  function setBadge(link, count) {
    let badge = link.querySelector('.member-unread-badge');

    if (!badge) {
      badge = document.createElement('span');
      badge.className = 'member-unread-badge';
      link.append(badge);
    }

    badge.hidden = count === 0;

    const text = count > 99 ? '99+' : String(count);

    if (badge.textContent !== text) {
      badge.textContent = text;
    }

    badge.setAttribute('aria-label', `${count} unread messages`);
    badge.title = `${count} unread messages`;
  }

  function decorateTicks() {
    messages?.querySelectorAll(
      '.message-row.sent[data-message-id]'
    ).forEach(row => {
      let tick = row.querySelector('.member-read-tick');

      if (
        row.dataset.deleted === 'true' ||
        row.dataset.deleted === '1'
      ) {
        tick?.remove();
        return;
      }

      const time = row.querySelector('.message-time');
      if (!time) return;

      if (!tick) {
        tick = document.createElement('span');
        tick.className = 'member-read-tick';
        time.append(tick);
      }

      const state = receipts.get(String(row.dataset.messageId));
      const seen = Boolean(state?.seen);
      const text = seen ? '✓✓' : '✓';

      if (tick.textContent !== text) {
        tick.textContent = text;
      }

      tick.classList.toggle('seen', seen);

      tick.title = mode === 'group' && state
        ? `Read by ${state.read_count} of ${state.reader_count} members`
        : seen
          ? 'Seen'
          : 'Sent · not seen yet';

      tick.setAttribute('aria-label', tick.title);
    });
  }

  function queueRefresh() {
    if (stopped) return;

    clearTimeout(refreshTimer);
    refreshTimer = setTimeout(refresh, 100);
  }

  async function refresh() {
    if (stopped || !root.isConnected) return;

    if (loading) {
      again = true;
      return;
    }

    loading = true;

    try {
      const url = new URL(metaUrl, location.href);

      if (targetId) {
        url.searchParams.set('kind', mode);
        url.searchParams.set('target_id', targetId);
      }

      const data = await request(url);
      if (stopped) return;

      const peers = new Map(
        data.personal.map(item => [
          String(item.peer_id),
          item.unread
        ])
      );

      const groups = new Map(
        data.groups.map(item => [
          String(item.group_id),
          item.unread
        ])
      );

      root.querySelectorAll(
        '.chat-user-row[data-peer-id]'
      ).forEach(link => {
        setBadge(link, peers.get(link.dataset.peerId) || 0);
      });

      root.querySelectorAll(
        '.chat-group-row[data-group-id]'
      ).forEach(link => {
        setBadge(link, groups.get(link.dataset.groupId) || 0);
      });

      receipts = new Map(
        data.receipts.map(item => [
          String(item.message_id),
          item
        ])
      );

      decorateTicks();
      queueRead();
    } catch (error) {
      if (error.name !== 'AbortError') {
        console.debug('Chat badges will retry.', error.message);
      }
    } finally {
      loading = false;

      if (again) {
        again = false;
        queueRefresh();
      }
    }
  }

  function queueRead() {
    clearTimeout(readTimer);

    if (!stopped) {
      readTimer = setTimeout(markRead, 180);
    }
  }

  function mayRead() {
    return (
      messages &&
      targetId &&
      !document.hidden &&
      document.hasFocus() &&
      messages.getClientRects().length > 0 &&
      messages.scrollHeight -
        messages.scrollTop -
        messages.clientHeight < 90 &&
      !root.querySelector('#memberMessageSearch')?.value.trim()
    );
  }

  async function markRead() {
    if (stopped || reading || !mayRead()) return;

    const ids = [
      ...messages.querySelectorAll('.message-row[data-message-id]')
    ]
      .filter(row => !row.hidden)
      .map(row => Number(row.dataset.messageId))
      .filter(Number.isSafeInteger);

    const latest = ids.length ? Math.max(...ids) : 0;

    if (!latest || latest <= acknowledged) return;

    const token = document.querySelector(
      '[name=csrfmiddlewaretoken]'
    )?.value;

    if (!token) return;

    reading = true;

    try {
      const body = new URLSearchParams({
        kind: mode,
        target_id: targetId,
        message_id: String(latest)
      });

      const data = await request(readUrl, {
        method: 'POST',
        headers: {
          'X-CSRFToken': token
        },
        body
      });

      acknowledged = Math.max(
        acknowledged,
        Number(data.last_read_id)
      );

      queueRefresh();
    } catch (error) {
      if (error.name !== 'AbortError') {
        console.debug('Read receipt will retry.', error.message);
      }
    } finally {
      reading = false;
    }
  }

  function connect() {
    if (stopped || !root.isConnected) return;

    const protocol = location.protocol === 'https:'
      ? 'wss:'
      : 'ws:';

    socket = new WebSocket(
      `${protocol}//${location.host}/ws/member/chat-updates/`
    );

    socket.onopen = queueRefresh;

    socket.onmessage = event => {
      try {
        if (JSON.parse(event.data).action === 'sync_chat_meta') {
          queueRefresh();
        }
      } catch (_) {
        // Ignore malformed socket payloads.
      }
    };

    socket.onclose = event => {
      if (!stopped && event.code !== 4403) {
        retry = setTimeout(connect, 2500);
      }
    };
  }

  const observer = new MutationObserver(changes => {
    const relevant = changes.some(change => {
      if (change.target.closest?.('.member-read-tick')) {
        return false;
      }

      if (change.target.closest?.('.message-text')) {
        return true;
      }

      return [
        ...change.addedNodes,
        ...change.removedNodes
      ].some(node => (
        node.nodeType === 1 &&
        (
          node.matches?.('.message-row,.message-time') ||
          node.querySelector?.('.message-row')
        )
      ));
    });

    if (relevant) {
      decorateTicks();
      queueRefresh();
      queueRead();
    }
  });

  if (messages) {
    observer.observe(messages, {
      childList: true,
      subtree: true
    });
  }

  listen(messages, 'scroll', queueRead);

  listen(window, 'focus', () => {
    queueRefresh();
    queueRead();
  });

  listen(document, 'visibilitychange', () => {
    if (!document.hidden) {
      queueRefresh();
      queueRead();
    }
  });

  listen(
    root.querySelector('#memberMessageSearch'),
    'input',
    queueRead
  );

  polling = setInterval(() => {
    if (!root.isConnected) {
      window.disposeMemberChatReceipts?.();
      return;
    }

    queueRefresh();
    queueRead();
  }, 15000);

  window.disposeMemberChatReceipts = () => {
    stopped = true;

    clearInterval(polling);
    [retry, refreshTimer, readTimer].forEach(clearTimeout);

    observer.disconnect();
    listeners.forEach(remove => remove());
    controllers.forEach(controller => controller.abort());

    socket?.close();
  };

  decorateTicks();
  refresh();
  connect();
})();