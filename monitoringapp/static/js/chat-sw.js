
"use strict";

// Receive Web Push notifications in the background.
self.addEventListener("push", (event) => {
    let data = {};

    try {
        data = event.data ? event.data.json() : {};
    } catch (error) {
        data = {
            title: "Cybexel Work Monitoring",
            body: "You have a new notification."
        };
    }

    const title = String(
        data.title || "Cybexel Work Monitoring"
    );

    const options = {
        body: String(data.body || "You have a new notification."),
        icon: "/static/images/logo.png",
        badge: "/static/images/logo.png",
        tag: String(data.tag || "cybexel-notification"),
        renotify: false,
        silent: false,
        data: {
            url: data.url || "/teamlead/notifications/"
        }
    };

    event.waitUntil(
        self.registration.showNotification(title, options)
    );
});

// Open the related page when the notification is clicked.
self.addEventListener("notificationclick", (event) => {
    event.notification.close();

    const requestedUrl = event.notification.data?.url
        || "/teamlead/notifications/";

    const target = new URL(requestedUrl, self.location.origin);

    if (target.origin !== self.location.origin) {
        return;
    }

    event.waitUntil((async () => {
        const windows = await clients.matchAll({
            type: "window",
            includeUncontrolled: true
        });

        for (const windowClient of windows) {
            if (windowClient.url === target.href) {
                return windowClient.focus();
            }
        }

        return clients.openWindow(target.href);
    })());
});
