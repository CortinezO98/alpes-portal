document.addEventListener("DOMContentLoaded", () => {
  const shell = document.querySelector("[data-dashboard-shell]");
  const toggleButton = document.querySelector("[data-sidebar-toggle]");
  const closeButtons = document.querySelectorAll("[data-sidebar-close]");
  if (!shell) return;

  const DESKTOP_BREAKPOINT = 1024;
  const STORAGE_KEY = "alpes.sidebar.collapsed";

  const isDesktop = () => window.innerWidth >= DESKTOP_BREAKPOINT;

  const setExpandedState = expanded => {
    toggleButton?.setAttribute("aria-expanded", String(expanded));
  };

  const openMobile = () => {
    shell.classList.add("sidebar-open");
    document.body.classList.add("dashboard-menu-open");
    setExpandedState(true);
  };

  const closeMobile = () => {
    shell.classList.remove("sidebar-open");
    document.body.classList.remove("dashboard-menu-open");
    setExpandedState(false);
  };

  const setDesktopCollapsed = collapsed => {
    shell.classList.toggle("sidebar-collapsed", collapsed);
    try {
      localStorage.setItem(STORAGE_KEY, collapsed ? "1" : "0");
    } catch (_) {}
    setExpandedState(!collapsed);
  };

  const restoreDesktopState = () => {
    if (!isDesktop()) {
      shell.classList.remove("sidebar-collapsed");
      closeMobile();
      return;
    }

    let collapsed = false;
    try {
      collapsed = localStorage.getItem(STORAGE_KEY) === "1";
    } catch (_) {}
    shell.classList.remove("sidebar-open");
    document.body.classList.remove("dashboard-menu-open");
    shell.classList.toggle("sidebar-collapsed", collapsed);
    setExpandedState(!collapsed);
  };

  toggleButton?.addEventListener("click", () => {
    if (isDesktop()) {
      setDesktopCollapsed(!shell.classList.contains("sidebar-collapsed"));
      return;
    }

    if (shell.classList.contains("sidebar-open")) closeMobile();
    else openMobile();
  });

  closeButtons.forEach(button => {
    button.addEventListener("click", () => {
      if (isDesktop()) setDesktopCollapsed(true);
      else closeMobile();
    });
  });

  document.addEventListener("keydown", event => {
    if (event.key !== "Escape") return;
    if (isDesktop()) setDesktopCollapsed(true);
    else closeMobile();
  });

  window.addEventListener("resize", restoreDesktopState);
  restoreDesktopState();
});