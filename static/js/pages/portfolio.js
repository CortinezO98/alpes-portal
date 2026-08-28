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

    const heroCopy = document.querySelector(".public-hero-copy");
    const heroPanel = document.querySelector(".public-hero-panel");

    if (!prefersReducedMotion.matches) {
        if (heroCopy) {
            heroCopy.style.setProperty("--animate-duration", "620ms");
        }
        if (heroPanel) {
            heroPanel.style.setProperty("--animate-duration", "680ms");
            heroPanel.style.animationDelay = "120ms";
        }
    }

    const revealGroups = [
        { selector: ".public-profile-grid > *", stagger: 70 },
        { selector: ".public-values-grid article", stagger: 65 },
        { selector: ".public-section-heading > *", stagger: 80 },
        { selector: ".public-service-card", stagger: 70 },
        { selector: ".public-model-intro", stagger: 0 },
        { selector: ".public-model-steps li", stagger: 75 },
        { selector: ".public-experience-grid > *", stagger: 85 },
        { selector: ".public-faq-grid > *", stagger: 85 },
        { selector: ".public-cta-inner > *", stagger: 85 },
    ];

    const revealElements = [];

    revealGroups.forEach(({ selector, stagger }) => {
        document.querySelectorAll(selector).forEach((element, index) => {
            element.dataset.revealDelay = String(index * stagger);
            revealElements.push(element);
        });
    });

    if (!prefersReducedMotion.matches && "IntersectionObserver" in window) {
        const revealObserver = new IntersectionObserver(
            (entries, observer) => {
                entries.forEach((entry) => {
                    if (!entry.isIntersecting) {
                        return;
                    }

                    const element = entry.target;
                    const delay = Number(element.dataset.revealDelay || 0);
                    element.style.setProperty("--animate-duration", "560ms");
                    element.style.animationDelay = `${delay}ms`;
                    element.classList.add("animate__animated", "animate__fadeInUp");
                    observer.unobserve(element);
                });
            },
            {
                threshold: 0.12,
                rootMargin: "0px 0px -7% 0px",
            },
        );

        revealElements.forEach((element) => revealObserver.observe(element));
    }

    syncHeader();
    window.addEventListener("scroll", syncHeader, { passive: true });
})();
