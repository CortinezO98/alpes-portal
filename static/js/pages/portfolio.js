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

    const serviceRoutes = [
        "/servicios/liderazgo/",
        "/servicios/jubilacion-plena/",
        "/servicios/consultoria-organizacional/",
        "/modelo-alpes/",
    ];

    document.querySelectorAll(".public-service-card").forEach((card, index) => {
        if (!serviceRoutes[index] || card.querySelector("[data-service-detail-link]")) {
            return;
        }

        const link = document.createElement("a");
        link.href = serviceRoutes[index];
        link.className = "public-service-detail-link";
        link.setAttribute("data-service-detail-link", "");
        link.textContent = "Conocer servicio →";

        const existingLink = card.querySelector(".public-text-link");
        if (existingLink) {
            existingLink.replaceWith(link);
        } else {
            card.appendChild(link);
        }
    });

    const whatsappHref =
        "https://wa.me/573107426028?text=Hola%2C%20quisiera%20conocer%20m%C3%A1s%20sobre%20los%20servicios%20ALPES.";

    if (!document.querySelector("[data-whatsapp-float]")) {
        const whatsappButton = document.createElement("a");
        whatsappButton.className = "public-whatsapp-float";
        whatsappButton.href = whatsappHref;
        whatsappButton.target = "_blank";
        whatsappButton.rel = "noopener noreferrer";
        whatsappButton.setAttribute("aria-label", "Escribir por WhatsApp a ALPES");
        whatsappButton.setAttribute("title", "Escribir por WhatsApp");
        whatsappButton.setAttribute("data-whatsapp-float", "");
        whatsappButton.innerHTML = `
            <svg viewBox="0 0 32 32" aria-hidden="true" focusable="false">
                <path d="M16.04 3.2a12.64 12.64 0 0 0-10.87 19.1L3.2 28.8l6.66-1.9a12.66 12.66 0 1 0 6.18-23.7Zm0 2.26a10.39 10.39 0 1 1-5.32 19.32l-.39-.23-3.95 1.13 1.16-3.84-.25-.4a10.38 10.38 0 0 1 8.75-15.98Zm-5.72 4.93c-.25 0-.65.1-.99.47-.34.37-1.3 1.27-1.3 3.1 0 1.82 1.33 3.59 1.51 3.84.19.25 2.62 4 6.35 5.61.89.38 1.58.61 2.12.78.89.28 1.7.24 2.34.15.71-.11 2.19-.9 2.5-1.76.31-.87.31-1.61.22-1.77-.09-.15-.34-.24-.71-.43-.37-.18-2.19-1.08-2.53-1.2-.34-.13-.59-.19-.84.18-.25.37-.96 1.2-1.18 1.45-.22.25-.43.28-.8.09-.37-.18-1.56-.57-2.97-1.83-1.1-.98-1.84-2.19-2.06-2.56-.22-.37-.02-.57.16-.75.17-.17.37-.43.56-.65.18-.22.25-.37.37-.62.12-.25.06-.47-.03-.65-.09-.19-.84-2.02-1.15-2.77-.3-.73-.61-.63-.84-.64h-.71Z"/>
            </svg>
        `;
        document.body.appendChild(whatsappButton);
    }

    syncHeader();
    window.addEventListener("scroll", syncHeader, { passive: true });
})();
