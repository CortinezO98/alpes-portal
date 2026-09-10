(() => {
    const header = document.querySelector("[data-public-header]");
    const menuButton = document.querySelector("[data-menu-button]");
    const navigation = document.querySelector("[data-public-nav]");
    const syncHeader = () => header?.classList.toggle("is-scrolled", window.scrollY > 8);
    const closeMenu = () => { navigation?.classList.remove("is-open"); menuButton?.setAttribute("aria-expanded", "false"); };

    if (menuButton && navigation) {
        menuButton.addEventListener("click", () => {
            const isOpen = navigation.classList.toggle("is-open");
            menuButton.setAttribute("aria-expanded", String(isOpen));
        });
        navigation.querySelectorAll("a").forEach((link) => link.addEventListener("click", closeMenu));
        window.addEventListener("resize", () => { if (window.innerWidth > 992) closeMenu(); });
    }

    const tabs = [...document.querySelectorAll("[data-service-tab]")];
    const panels = [...document.querySelectorAll("[data-service-panel]")];
    const activateTab = (tab, focus = false) => {
        const service = tab.dataset.serviceTab;
        tabs.forEach((item) => {
            const selected = item === tab;
            item.classList.toggle("is-active", selected);
            item.setAttribute("aria-selected", String(selected));
            if (selected && focus) item.focus();
        });
        panels.forEach((panel) => { panel.hidden = panel.dataset.servicePanel !== service; });
    };
    tabs.forEach((tab, index) => {
        tab.addEventListener("click", () => activateTab(tab));
        tab.addEventListener("keydown", (event) => {
            if (!["ArrowDown", "ArrowUp", "ArrowRight", "ArrowLeft", "Home", "End"].includes(event.key)) return;
            event.preventDefault();
            const nextIndex = event.key === "Home" ? 0 : event.key === "End" ? tabs.length - 1 : (index + (event.key === "ArrowDown" || event.key === "ArrowRight" ? 1 : -1) + tabs.length) % tabs.length;
            activateTab(tabs[nextIndex], true);
        });
    });

    const whatsappHref = "https://wa.me/573107426028?text=Hola%2C%20quisiera%20conocer%20m%C3%A1s%20sobre%20los%20servicios%20ALPES.";
    if (!document.querySelector("[data-whatsapp-float]")) {
        const link = document.createElement("a");
        link.className = "public-whatsapp-float";
        link.href = whatsappHref;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        link.setAttribute("aria-label", "Escribir por WhatsApp a ALPES");
        link.setAttribute("data-whatsapp-float", "");
        link.textContent = "◔";
        document.body.appendChild(link);
    }
    syncHeader();
    window.addEventListener("scroll", syncHeader, { passive: true });
})();