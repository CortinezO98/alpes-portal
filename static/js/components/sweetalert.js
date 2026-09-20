document.addEventListener("DOMContentLoaded", () => {
  if (typeof Swal === "undefined") return;

  const palette = {
    primary: "#176b68",
    primaryDark: "#125b57",
    background: "#f7f4ec",
    text: "#333333",
    border: "#83bdb7",
    accent: "#c69a45",
    danger: "#8f4c4c",
  };

  const levelToIcon = level => {
    if (level.includes("error") || level.includes("danger")) return "error";
    if (level.includes("warning")) return "warning";
    if (level.includes("success")) return "success";
    return "info";
  };

  const notificationNodes = [...document.querySelectorAll("[data-alpes-notification]")];

  notificationNodes.forEach((node, index) => {
    const level = node.dataset.level || "info";
    const message = node.dataset.message || "";
    const icon = levelToIcon(level);
    const isError = icon === "error";
    const isWarning = icon === "warning";

    window.setTimeout(() => {
      if (isError || isWarning) {
        Swal.fire({
          icon,
          title: isError ? "Revisa la información" : "Atención",
          text: message,
          confirmButtonText: "Entendido",
          confirmButtonColor: palette.primary,
          background: palette.background,
          color: palette.text,
          customClass: {
            popup: "alpes-swal-popup",
            confirmButton: "alpes-swal-confirm",
          },
        });
        return;
      }

      Swal.fire({
        toast: true,
        position: "top-end",
        icon,
        title: message,
        showConfirmButton: false,
        timer: 3600,
        timerProgressBar: true,
        background: palette.background,
        color: palette.text,
        customClass: {
          popup: "alpes-swal-toast",
        },
        didOpen: toast => {
          toast.addEventListener("mouseenter", Swal.stopTimer);
          toast.addEventListener("mouseleave", Swal.resumeTimer);
        },
      });
    }, index * 180);
  });

  document.addEventListener("submit", async event => {
    const form = event.target.closest("form[data-swal-confirm='true']");
    if (!form || form.dataset.swalConfirmed === "true") return;

    event.preventDefault();

    const result = await Swal.fire({
      icon: form.dataset.swalIcon || "question",
      title: form.dataset.swalTitle || "¿Confirmar acción?",
      text: form.dataset.swalText || "Esta acción requiere confirmación.",
      showCancelButton: true,
      confirmButtonText: form.dataset.swalConfirmText || "Sí, continuar",
      cancelButtonText: form.dataset.swalCancelText || "Cancelar",
      confirmButtonColor: palette.primary,
      cancelButtonColor: "#6f7f7a",
      reverseButtons: true,
      focusCancel: true,
      background: palette.background,
      color: palette.text,
      customClass: {
        popup: "alpes-swal-popup",
        confirmButton: "alpes-swal-confirm",
        cancelButton: "alpes-swal-cancel",
      },
    });

    if (!result.isConfirmed) return;

    form.dataset.swalConfirmed = "true";
    form.submit();
  });

  window.AlpesAlert = {
    success(message, title = "Listo") {
      return Swal.fire({
        icon: "success",
        title,
        text: message,
        confirmButtonText: "Aceptar",
        confirmButtonColor: palette.primary,
        background: palette.background,
        color: palette.text,
        customClass: { popup: "alpes-swal-popup" },
      });
    },
    error(message, title = "No fue posible completar la acción") {
      return Swal.fire({
        icon: "error",
        title,
        text: message,
        confirmButtonText: "Entendido",
        confirmButtonColor: palette.primary,
        background: palette.background,
        color: palette.text,
        customClass: { popup: "alpes-swal-popup" },
      });
    },
    info(message, title = "Información") {
      return Swal.fire({
        icon: "info",
        title,
        text: message,
        confirmButtonText: "Entendido",
        confirmButtonColor: palette.primary,
        background: palette.background,
        color: palette.text,
        customClass: { popup: "alpes-swal-popup" },
      });
    },
    confirm(options = {}) {
      return Swal.fire({
        icon: options.icon || "question",
        title: options.title || "¿Confirmar acción?",
        text: options.text || "",
        showCancelButton: true,
        confirmButtonText: options.confirmText || "Sí, continuar",
        cancelButtonText: options.cancelText || "Cancelar",
        confirmButtonColor: palette.primary,
        cancelButtonColor: "#6f7f7a",
        reverseButtons: true,
        focusCancel: true,
        background: palette.background,
        color: palette.text,
        customClass: { popup: "alpes-swal-popup" },
      });
    },
  };
});