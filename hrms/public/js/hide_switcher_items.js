// console.log("Monkey patch Loaded.");

function hideMenuItems() {
    const menu = document.querySelector(".app-switcher-menu");
    if (!menu) {
        console.warn("App switcher not ready");
        return;
    }

    const removeItem = (name) => {
        const el = menu.querySelector(`[data-app-name="${name}"]`);
        if (el) el.remove();
    };

    removeItem("website");
    removeItem("settings");
}

// Observe the DOM for dynamically added App Switcher menu
const observer = new MutationObserver(() => hideMenuItems());
observer.observe(document.body, { childList: true, subtree: true });

// Also run once in case the menu already exists
setTimeout(hideMenuItems, 500);
