/* Shared activity tracking and live presence dots. */
(function () {
    'use strict';
    if (window.cybexelActivityInitialized) return;
    window.cybexelActivityInitialized = true;
    const refreshInterval = 30000;
    let lastActivitySent = 0;
    let activityPending = false;
    const pendingStatuses = new Map();

    function csrfToken() {
        const match = document.cookie.split(';').map(value => value.trim())
            .find(value => value.startsWith('csrftoken='));
        return match ? decodeURIComponent(match.slice('csrftoken='.length)) :
            (document.querySelector('[name="csrfmiddlewaretoken"]')?.value || '');
    }

    function applyStatus(userId, status, suppliedDot) {
        if (status !== 'active' && status !== 'inactive') return;
        const active = status === 'active';
        const label = active ? 'Active' : 'Inactive';
        const dots = new Set(document.querySelectorAll('.user-status-dot[data-user-id="' + userId + '"]'));
        if (suppliedDot?.isConnected) dots.add(suppliedDot);
        dots.forEach(dot => {
            dot.dataset.status = status;
            dot.title = label;
            dot.setAttribute('aria-label', label);
            dot.classList.toggle('bg-green-500', active);
            dot.classList.toggle('bg-red-500', !active);
            // Works with plain CSS as well as pages that load Tailwind.
            dot.style.backgroundColor = active ? '#45dc91' : '#ff6978';
            dot.style.boxShadow = active ? '0 0 8px rgba(69,220,145,.4)' : '0 0 8px rgba(255,105,120,.35)';
        });
        document.querySelectorAll('[data-user-status="' + userId + '"]').forEach(badge => {
            badge.dataset.status = status;
            badge.classList.toggle('status-active', active);
            badge.classList.toggle('status-inactive', !active);
            badge.textContent = label;
        });
    }

    window.updateStatusDot = function (userId, dotElement) {
        userId = String(userId);
        if (!/^\d+$/.test(userId)) return Promise.resolve();
        if (pendingStatuses.has(userId)) return pendingStatuses.get(userId);
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 10000);
        const pending = fetch('/api/user-status/' + userId + '/', {
            credentials: 'same-origin', cache: 'no-store', signal: controller.signal
        }).then(response => {
            if (!response.ok) return null;
            return response.json();
        }).then(data => {
            if (data?.success) applyStatus(userId, data.status, dotElement);
        }).catch(() => {
            // Keep the last known state when the network is unavailable.
        }).finally(() => { clearTimeout(timeout); pendingStatuses.delete(userId); });
        pendingStatuses.set(userId, pending);
        return pending;
    };

    window.refreshAllStatusDots = function () {
        if (document.hidden) return;
        const ids = new Set(Array.from(document.querySelectorAll('.user-status-dot[data-user-id]'))
            .map(dot => dot.dataset.userId));
        ids.forEach(id => window.updateStatusDot(id));
    };

    function updateActivity() {
        const now = Date.now();
        if (document.hidden || activityPending || now - lastActivitySent < refreshInterval) return;
        activityPending = true;
        lastActivitySent = now;
        fetch('/api/update-activity/', {
            method: 'POST', credentials: 'same-origin', cache: 'no-store',
            headers: {'X-CSRFToken': csrfToken(), 'Content-Type': 'application/json'}
        }).then(response => response.ok ? response.json() : null)
          .then(data => { if (data?.success) window.refreshAllStatusDots(); })
          .catch(() => { lastActivitySent = 0; })
          .finally(() => { activityPending = false; });
    }

    ['mousemove', 'mousedown', 'keydown', 'click', 'touchstart'].forEach(event => {
        document.addEventListener(event, updateActivity, {passive: true});
    });
    document.addEventListener('scroll', updateActivity, {passive: true, capture: true});

    function initialize() {
        window.refreshAllStatusDots();
        setInterval(window.refreshAllStatusDots, refreshInterval);
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) window.refreshAllStatusDots();
        });
        // Search/filter replaces these rows without reloading the page.
        const tableBody = document.getElementById('employeeTableBody');
        if (tableBody) {
            let timer;
            new MutationObserver(records => {
                if (!records.some(record => Array.from(record.addedNodes).some(node =>
                    node.nodeType === 1 && (node.matches?.('.user-status-dot') || node.querySelector?.('.user-status-dot'))))) return;
                clearTimeout(timer);
                timer = setTimeout(window.refreshAllStatusDots, 150);
            }).observe(tableBody, {childList: true, subtree: true});
        }
    }
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initialize, {once: true});
    else initialize();
})();
