// ===============================
// USER ACTIVITY TRACKING
// ===============================

(function () {
    let lastActivitySent = 0;

    function getCookie(name) {
        let cookieValue = null;

        if (document.cookie && document.cookie !== "") {
            const cookies = document.cookie.split(";");

            for (let cookie of cookies) {
                cookie = cookie.trim();

                if (cookie.startsWith(name + "=")) {
                    cookieValue = decodeURIComponent(
                        cookie.substring(name.length + 1)
                    );
                    break;
                }
            }
        }

        return cookieValue;
    }

    function updateActivity() {
        const now = Date.now();

        // Prevent too many API requests
        if (now - lastActivitySent < 30000) {
            return;
        }

        lastActivitySent = now;

        fetch("/api/update-activity/", {
            method: "POST",
            headers: {
                "X-CSRFToken": getCookie("csrftoken"),
                "Content-Type": "application/json"
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error("Activity update failed");
            }

            return response.json();
        })
        .then(data => {
            if (data.success) {
                console.log("User activity updated:", data.status);
            }
        })
        .catch(error => {
            console.error("Activity update error:", error);
        });
    }

    // Track user activity
    document.addEventListener("mousemove", updateActivity);
    document.addEventListener("mousedown", updateActivity);
    document.addEventListener("keydown", updateActivity);
    document.addEventListener("click", updateActivity);
    document.addEventListener("scroll", updateActivity);

})();


function updateStatusDot(userId, dotElement) {
    fetch(`/api/user-status/${userId}/`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (data.status === "active") {
                    dotElement.classList.remove("bg-red-500");
                    dotElement.classList.add("bg-green-500");
                    dotElement.title = "Active";
                } else {
                    dotElement.classList.remove("bg-green-500");
                    dotElement.classList.add("bg-red-500");
                    dotElement.title = "Inactive";
                }
            }
        })
        .catch(error => {
            console.error("Status update error:", error);
        });
}


function refreshAllStatusDots() {
    const dots = document.querySelectorAll(".user-status-dot");

    dots.forEach(dot => {
        const userId = dot.dataset.userId;

        if (userId) {
            updateStatusDot(userId, dot);
        }
    });
}

refreshAllStatusDots();

setInterval(refreshAllStatusDots, 30000);