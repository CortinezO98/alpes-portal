(() => {
    const header = document.querySelector("[data-public-header]");
    const menuButton = document.querySelector("[data-menu-button]");
    const navigation = document.querySelector("[data-public-nav]");

    const syncHeader = () => {
        if (!header) {
            return;
        }
        header.classList.toggle("is-scrolled", window.scrollY > 8);
    };

    const closeMenu = () => {
        if (!menuButton || !navigation) {
            return;
        }
        navigation.classList.remove("is-open");
        menuButton.setAttribute("aria-expanded", "false");
    };

    if (menuButton && navigation) {
        menuButton.addEventListener("click", () => {
            const isOpen = navigation.classList.toggle("is-open");
            menuButton.setAttribute("aria-expanded", String(isOpen));
        });

        navigation.querySelectorAll("a").forEach((link) => {
            link.addEventListener("click", closeMenu);
        });

        window.addEventListener("resize", () => {
            if (window.innerWidth > 992) {
                closeMenu();
            }
        });
    }

    syncHeader();
    window.addEventListener("scroll", syncHeader, { passive: true });
})();
