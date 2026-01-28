(() => {
//    console.log("Employee Panel Hide Script Loaded");

    function hideEmployeePanels() {
        const panels = document.querySelectorAll(
            ".form-dashboard-section.form-heatmap, .form-dashboard-section.form-links"
        );

        if (!panels.length) {
            return;
        }

        panels.forEach(panel => panel.style.display = "none");
    }

    const observer = new MutationObserver(() => hideEmployeePanels());
    observer.observe(document.body, { childList: true, subtree: true });

    setTimeout(hideEmployeePanels, 500);
})();
