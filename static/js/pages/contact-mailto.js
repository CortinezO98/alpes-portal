(() => {
    const form = document.querySelector("[data-contact-form]");

    if (!form) {
        return;
    }

    const status = form.querySelector("[data-contact-status]");

    form.addEventListener("submit", (event) => {
        event.preventDefault();

        if (!form.checkValidity()) {
            form.reportValidity();
            return;
        }

        const data = new FormData(form);
        const interest = data.get("interest");
        const subject = `Consulta web: ${interest}`;
        const body = [
            `Nombre: ${data.get("name")}`,
            `Correo: ${data.get("email")}`,
            `Empresa: ${data.get("company") || "No indicada"}`,
            `Interés: ${interest}`,
            "",
            "Mensaje:",
            data.get("message"),
        ].join("\n");

        if (status) {
            status.textContent = "Se abrirá tu aplicación de correo con el mensaje preparado.";
        }

        window.location.href = `mailto:Josemarrugo@hotmail.com?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
    });
})();
