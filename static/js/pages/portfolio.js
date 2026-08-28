(() => {
    const header = document.querySelector("[data-public-header]");
    const menuButton = document.querySelector("[data-menu-button]");
    const navigation = document.querySelector("[data-public-nav]");
    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

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

    const revealGroups = [
        { selector: ".public-profile-grid > *", stagger: 90 },
        { selector: ".public-values-grid article", stagger: 75 },
        { selector: ".public-section-heading > *", stagger: 90 },
        { selector: ".public-service-card", stagger: 85 },
        { selector: ".public-model-intro", stagger: 0 },
        { selector: ".public-model-steps li", stagger: 90 },
        { selector: ".public-experience-grid > *", stagger: 100 },
        { selector: ".public-faq-grid > *", stagger: 100 },
        { selector: ".public-cta-inner > *", stagger: 100 },
    ];

    const revealElements = [];

    revealGroups.forEach(({ selector, stagger }) => {
        document.querySelectorAll(selector).forEach((element, index) => {
            element.classList.add("public-reveal");
            element.style.setProperty("--reveal-delay", `${index * stagger}ms`);
            revealElements.push(element);
        });
    });

    if (prefersReducedMotion.matches || !("IntersectionObserver" in window)) {
        revealElements.forEach((element) => element.classList.add("is-visible"));
    } else {
        const revealObserver = new IntersectionObserver(
            (entries, observer) => {
                entries.forEach((entry) => {
                    if (!entry.isIntersecting) {
                        return;
                    }
                    entry.target.classList.add("is-visible");
                    observer.unobserve(entry.target);
                });
            },
            {
                threshold: 0.12,
                rootMargin: "0px 0px -8% 0px",
            },
        );

        revealElements.forEach((element) => revealObserver.observe(element));
    }

    syncHeader();
    window.addEventListener("scroll", syncHeader, { passive: true });
})();
