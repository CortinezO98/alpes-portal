document.addEventListener("DOMContentLoaded", () => {
  const shell = document.querySelector("[data-dashboard-shell]");
  const openButton = document.querySelector("[data-sidebar-open]");
  const closeButtons = document.querySelectorAll("[data-sidebar-close]");
  if (!shell) return;

  const open = () => {
    shell.classList.add("sidebar-open");
    document.body.classList.add("dashboard-menu-open");
  };
  const close = () => {
    shell.classList.remove("sidebar-open");
    document.body.classList.remove("dashboard-menu-open");
  };

  openButton?.addEventListener("click", open);
  closeButtons.forEach(button => button.addEventListener("click", close));

  document.addEventListener("keydown", event => {
    if (event.key === "Escape") close();
  });

  window.addEventListener("resize", () => {
    if (window.innerWidth >= 1024) close();
  });
});