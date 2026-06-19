(function () {
    const toggle = document.querySelector("[data-admin-sidebar-toggle]");
    const sidebar = document.getElementById("admin-sidebar");
    const storageKey = "nobleAdminSidebarHidden";

    if (!toggle || !sidebar) {
        return;
    }

    function readStoredState() {
        try {
            return window.localStorage.getItem(storageKey) === "true";
        } catch (error) {
            return false;
        }
    }

    function storeState(isHidden) {
        try {
            window.localStorage.setItem(storageKey, String(isHidden));
        } catch (error) {
            // The toggle still works if browser storage is unavailable.
        }
    }

    function applyState(isHidden) {
        document.body.classList.toggle("admin-sidebar-hidden", isHidden);
        toggle.setAttribute("aria-expanded", String(!isHidden));
        toggle.setAttribute(
            "aria-label",
            isHidden ? "Show dashboard navigation" : "Hide dashboard navigation"
        );
        toggle.title = isHidden ? "Show navigation" : "Hide navigation";
    }

    applyState(readStoredState());

    toggle.addEventListener("click", function () {
        const isHidden = !document.body.classList.contains("admin-sidebar-hidden");
        applyState(isHidden);
        storeState(isHidden);
    });
})();
