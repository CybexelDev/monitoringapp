
/*
 * Cybexel Windows Push Notifications
 * Reusable browser subscription manager.
 *
 * Usage:
 * CybexelWindowsPush.enable("team_lead")
 * CybexelWindowsPush.disable("team_lead")
 * CybexelWindowsPush.status("team_lead")
 */

(function () {
    "use strict";

    const ALLOWED_PORTALS = [
        "team_lead",
        "team_member",
        "management",
        "master_admin"
    ];

    const SERVICE_WORKER_URL = "/chat-sw.js";

    function validatePortal(portal) {
        if (!ALLOWED_PORTALS.includes(portal)) {
            throw new Error("Unsupported notification portal.");
        }
    }

    function apiUrl(portal, action) {
        validatePortal(portal);

        return (
            "/api/chat/push/" +
            encodeURIComponent(portal) +
            "/" + action + "/"
        );
    }

    function base64ToUint8Array(base64String) {
        const padding = "=".repeat(
            (4 - base64String.length % 4) % 4
        );

        const base64 = (
            base64String
                .replace(/-/g, "+")
                .replace(/_/g, "/") + padding
        );

        const decoded = atob(base64);

        return Uint8Array.from(
            decoded,
            char => char.charCodeAt(0)
        );
    }

    function supported() {
        return (
            window.isSecureContext &&
            "serviceWorker" in navigator &&
            "PushManager" in window &&
            "Notification" in window
        );
    }

    async function getConfig(portal) {
        const response = await fetch(
            apiUrl(portal, "config"),
            {
                credentials: "same-origin",
                cache: "no-store"
            }
        );

        const data = await response.json();

        if (!response.ok || !data.ok) {
            throw new Error(
                data.message || "Unable to load push settings."
            );
        }

        if (!data.configured || !data.public_key) {
            throw new Error(
                "VAPID configuration is not ready."
            );
        }

        return data;
    }

    async function registerWorker() {
        if (!supported()) {
            throw new Error(
                "Push notifications are not supported here."
            );
        }

        return navigator.serviceWorker.register(
            SERVICE_WORKER_URL,
            { scope: "/" }
        );
    }

    function getCsrfToken() {
        const match = document.cookie.match(
            /(?:^|;\s*)csrftoken=([^;]+)/
        );

        return match
            ? decodeURIComponent(match[1])
            : "";
    }

    async function postSubscription(portal, action, payload) {
        const response = await fetch(
            apiUrl(portal, action),
            {
                method: "POST",
                credentials: "same-origin",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCsrfToken()
                },
                body: JSON.stringify(payload)
            }
        );

        const data = await response.json();

        if (!response.ok || !data.ok) {
            throw new Error(
                data.message || "Unable to update subscription."
            );
        }

        return data;
    }

    async function enable(portal) {
        validatePortal(portal);

        // Call enable() from a real user button click.
        if (!supported()) {
            throw new Error(
                "Use Chrome or Edge on localhost or HTTPS."
            );
        }

        const config = await getConfig(portal);

        const permission = await Notification.requestPermission();

        if (permission !== "granted") {
            throw new Error(
                "Notification permission was not granted."
            );
        }

        const registration = await registerWorker();

        let subscription =
            await registration.pushManager.getSubscription();

        const applicationServerKey =
            base64ToUint8Array(config.public_key);

        if (!subscription) {
            subscription =
                await registration.pushManager.subscribe({
                    userVisibleOnly: true,
                    applicationServerKey
                });
        }

        await postSubscription(
            portal,
            "subscribe",
            subscription.toJSON()
        );

        return {
            ok: true,
            message: "Windows notifications enabled."
        };
    }

    async function disable(portal) {
        validatePortal(portal);

        if (!supported()) {
            throw new Error("Push notifications unsupported.");
        }

        const registration =
            await navigator.serviceWorker.getRegistration("/");

        if (!registration) {
            return {
                ok: true,
                message: "No notification registration found."
            };
        }

        const subscription =
            await registration.pushManager.getSubscription();

        if (!subscription) {
            return {
                ok: true,
                message: "Notifications already disabled."
            };
        }

        await postSubscription(
            portal,
            "unsubscribe",
            { endpoint: subscription.endpoint }
        );

        await subscription.unsubscribe();

        return {
            ok: true,
            message: "Windows notifications disabled."
        };
    }

    async function status(portal) {
        validatePortal(portal);

        if (!supported()) {
            return {
                supported: false,
                enabled: false
            };
        }

        const registration =
            await navigator.serviceWorker.getRegistration("/");

        const subscription = registration
            ? await registration.pushManager.getSubscription()
            : null;

        return {
            supported: true,
            permission: Notification.permission,
            enabled: (
                Notification.permission === "granted" &&
                Boolean(subscription)
            )
        };
    }

    window.CybexelWindowsPush = Object.freeze({
        enable,
        disable,
        status,
        supported
    });
})();
