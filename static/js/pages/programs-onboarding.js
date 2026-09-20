document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("engagement-onboarding-form");
  if (!form) return;

  const modeInputs = [...form.querySelectorAll('input[name="mode"]')];
  const programSelect = document.getElementById("id_program");
  const titleInput = document.getElementById("id_title");
  const organizationSection = document.getElementById("organization-section");
  const organizationSelect = document.getElementById("id_organization");
  const createOrganizationInput = document.getElementById("id_create_organization");
  const organizationNameInput = document.getElementById("id_organization_name");
  const organizationTaxInput = document.getElementById("id_organization_tax_id");
  const organizationContactNameInput = document.getElementById("id_organization_contact_name");
  const organizationContactEmailInput = document.getElementById("id_organization_contact_email");
  const organizationChip = document.getElementById("new-organization-chip");
  const organizationChipName = document.getElementById("new-organization-chip-name");
  const clearNewOrganization = document.getElementById("clear-new-organization");

  const modalOrganizationName = document.getElementById("modal_organization_name");
  const modalOrganizationTax = document.getElementById("modal_organization_tax_id");
  const modalOrganizationContactName = document.getElementById("modal_organization_contact_name");
  const modalOrganizationContactEmail = document.getElementById("modal_organization_contact_email");
  const saveNewOrganization = document.getElementById("save-new-organization");
  const organizationModalError = document.getElementById("organization-modal-error");
  const organizationModalElement = document.getElementById("organizationModal");

  const participantSearch = document.getElementById("participant-search");
  const participantOptions = [...document.querySelectorAll(".participant-option")];
  const existingChecks = [...document.querySelectorAll(".participant-existing-check")];
  const selectedParticipants = document.getElementById("selected-participants");
  const selectedChips = document.getElementById("selected-chips");
  const participantCount = document.getElementById("participant-count");
  const participantNoResults = document.getElementById("participant-no-results");
  const hiddenParticipants = document.getElementById("id_new_participants_json");

  const modalParticipantFirstName = document.getElementById("modal_participant_first_name");
  const modalParticipantLastName = document.getElementById("modal_participant_last_name");
  const modalParticipantEmail = document.getElementById("modal_participant_email");
  const modalParticipantPassword = document.getElementById("modal_participant_password");
  const participantModalError = document.getElementById("participant-modal-error");
  const participantModalElement = document.getElementById("participantModal");
  const saveNewParticipant = document.getElementById("save-new-participant");
  const generatePassword = document.getElementById("generate-password");
  const togglePassword = document.getElementById("toggle-password");

  const assignAssessment = document.getElementById("id_assign_assessment");
  const assessmentTemplateWrap = document.getElementById("assessment-template-wrap");
  const summaryProgram = document.getElementById("summary-program");
  const summaryMode = document.getElementById("summary-mode");
  const summaryOrganization = document.getElementById("summary-organization");
  const summaryParticipants = document.getElementById("summary-participants");
  const summaryAssessment = document.getElementById("summary-assessment");
  const mobileParticipantCount = document.getElementById("mobile-participant-count");
  const mobileSummaryMode = document.getElementById("mobile-summary-mode");
  const submitButtons = [...document.querySelectorAll(".onboarding-submit, .onboarding-submit-mobile")];

  let newParticipants = [];
  let titleWasEdited = Boolean(titleInput?.value?.trim());

  function selectedMode() {
    return modeInputs.find(input => input.checked)?.value || "ORGANIZATIONAL";
  }

  function selectedModeLabel() {
    return selectedMode() === "ORGANIZATIONAL" ? "Empresarial" : "Individual";
  }

  function isCreatingOrganization() {
    return createOrganizationInput?.value === "on" || createOrganizationInput?.value === "True";
  }

  function setCreateOrganization(active) {
    if (!createOrganizationInput) return;
    createOrganizationInput.value = active ? "on" : "";
  }

  function selectedOrganizationName() {
    if (selectedMode() === "INDIVIDUAL") return "No aplica";
    if (isCreatingOrganization()) return organizationNameInput?.value?.trim() || "Empresa nueva";
    if (!organizationSelect?.value) return "Por seleccionar";
    return organizationSelect.selectedOptions[0]?.text || "Por seleccionar";
  }

  function resetOrganizationModalError() {
    organizationModalError?.classList.add("d-none");
    if (organizationModalError) organizationModalError.textContent = "";
  }

  function showOrganizationModalError(message) {
    if (!organizationModalError) return;
    organizationModalError.textContent = message;
    organizationModalError.classList.remove("d-none");
  }

  function hydrateOrganizationModal() {
    if (modalOrganizationName) modalOrganizationName.value = organizationNameInput?.value || "";
    if (modalOrganizationTax) modalOrganizationTax.value = organizationTaxInput?.value || "";
    if (modalOrganizationContactName) modalOrganizationContactName.value = organizationContactNameInput?.value || "";
    if (modalOrganizationContactEmail) modalOrganizationContactEmail.value = organizationContactEmailInput?.value || "";
    resetOrganizationModalError();
  }

  function renderOrganizationState() {
    const enterprise = selectedMode() === "ORGANIZATIONAL";
    organizationSection?.classList.toggle("is-hidden", !enterprise);

    if (!enterprise) {
      setCreateOrganization(false);
      if (organizationSelect) organizationSelect.value = "";
    }

    const creating = enterprise && isCreatingOrganization();
    organizationChip?.classList.toggle("d-none", !creating);

    if (organizationSelect) {
      organizationSelect.disabled = creating || !enterprise;
      organizationSelect.closest(".flex-grow-1")?.classList.toggle("opacity-50", creating);
    }
    if (organizationChipName && creating) {
      organizationChipName.textContent = organizationNameInput?.value?.trim() || "Empresa nueva";
    }
  }

  function clearOrganizationDraft() {
    setCreateOrganization(false);
    [organizationNameInput, organizationTaxInput, organizationContactNameInput, organizationContactEmailInput].forEach(input => {
      if (input) input.value = "";
    });
    renderOrganizationState();
    suggestTitle();
    updateSummary();
  }

  function resetParticipantModal() {
    [modalParticipantFirstName, modalParticipantLastName, modalParticipantEmail, modalParticipantPassword].forEach(input => {
      if (input) input.value = "";
    });
    if (modalParticipantPassword) modalParticipantPassword.type = "password";
    participantModalError?.classList.add("d-none");
    if (participantModalError) participantModalError.textContent = "";
    togglePassword?.querySelector("i")?.classList.replace("bi-eye-slash", "bi-eye");
  }

  function showParticipantError(message) {
    if (!participantModalError) return;
    participantModalError.textContent = message;
    participantModalError.classList.remove("d-none");
  }

  function allSelectedExisting() {
    return participantOptions
      .filter(option => option.querySelector(".participant-existing-check")?.checked)
      .map(option => ({
        type: "existing",
        id: option.querySelector(".participant-existing-check").value,
        name: option.dataset.name,
        email: option.dataset.email,
      }));
  }

  function persistNewParticipants() {
    if (hiddenParticipants) hiddenParticipants.value = JSON.stringify(newParticipants);
  }

  function renderSelectedParticipants() {
    const selected = allSelectedExisting();
    selectedChips.innerHTML = "";

    const chips = [
      ...selected.map(item => ({ ...item, key: `existing-${item.id}` })),
      ...newParticipants.map((item, index) => ({
        ...item,
        type: "new",
        key: `new-${index}`,
        name: [item.first_name, item.last_name].filter(Boolean).join(" ") || item.email,
        index,
      })),
    ];

    chips.forEach(item => {
      const chip = document.createElement("span");
      chip.className = "selected-person-chip";
      chip.innerHTML = `
        <span>${escapeHtml(item.name)}</span>
        <button type="button" aria-label="Quitar ${escapeHtml(item.name)}"><i class="bi bi-x"></i></button>
      `;
      chip.querySelector("button").addEventListener("click", () => {
        if (item.type === "existing") {
          const checkbox = existingChecks.find(input => input.value === String(item.id));
          if (checkbox) checkbox.checked = false;
        } else {
          newParticipants.splice(item.index, 1);
          persistNewParticipants();
        }
        renderSelectedParticipants();
        updateSummary();
      });
      selectedChips.appendChild(chip);
    });

    selectedParticipants?.classList.toggle("d-none", chips.length === 0);
    participantCount.textContent = String(chips.length);
    if (mobileParticipantCount) mobileParticipantCount.textContent = String(chips.length);
  }

  function currentParticipantTotal() {
    return allSelectedExisting().length + newParticipants.length;
  }

  function updateSummary() {
    const modeLabel = selectedModeLabel();
    if (summaryMode) summaryMode.textContent = modeLabel;
    if (mobileSummaryMode) mobileSummaryMode.textContent = modeLabel;
    if (summaryOrganization) summaryOrganization.textContent = selectedOrganizationName();
    if (summaryProgram) summaryProgram.textContent = programSelect?.selectedOptions[0]?.text || "Por seleccionar";
    if (summaryParticipants) summaryParticipants.textContent = String(currentParticipantTotal());
    if (summaryAssessment) summaryAssessment.textContent = assignAssessment?.checked ? "Automática" : "Sin asignar";
    if (assessmentTemplateWrap) assessmentTemplateWrap.classList.toggle("is-hidden", !assignAssessment?.checked);
  }

  function suggestTitle() {
    if (!titleInput || titleWasEdited) return;
    const program = programSelect?.selectedOptions[0]?.text?.trim();
    const organization = selectedMode() === "ORGANIZATIONAL" ? selectedOrganizationName() : "Individual";
    const year = new Date().getFullYear();
    if (program && organization && organization !== "Por seleccionar") {
      titleInput.value = `${program} · ${organization} · ${year}`;
    }
  }

  function filterParticipants() {
    const query = participantSearch?.value?.trim().toLowerCase() || "";
    let visible = 0;
    participantOptions.forEach(option => {
      const matches = !query || option.dataset.search.includes(query);
      option.classList.toggle("is-hidden", !matches);
      if (matches) visible += 1;
    });
    participantNoResults?.classList.toggle("d-none", visible !== 0 || !query);
  }

  function generateSecurePassword() {
    const alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789!@#$%";
    const bytes = new Uint32Array(14);
    crypto.getRandomValues(bytes);
    return Array.from(bytes, value => alphabet[value % alphabet.length]).join("");
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  try {
    const raw = hiddenParticipants?.value;
    if (raw) {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) newParticipants = parsed;
    }
  } catch (_) {
    newParticipants = [];
  }
  persistNewParticipants();

  organizationModalElement?.addEventListener("show.bs.modal", hydrateOrganizationModal);
  saveNewOrganization?.addEventListener("click", () => {
    const name = modalOrganizationName?.value?.trim() || "";
    const email = modalOrganizationContactEmail?.value?.trim() || "";

    if (!name) {
      showOrganizationModalError("Escribe el nombre o razón social de la empresa.");
      modalOrganizationName?.focus();
      return;
    }
    if (email && !modalOrganizationContactEmail.checkValidity()) {
      showOrganizationModalError("El correo de contacto no tiene un formato válido.");
      modalOrganizationContactEmail?.focus();
      return;
    }

    setCreateOrganization(true);
    if (organizationNameInput) organizationNameInput.value = name;
    if (organizationTaxInput) organizationTaxInput.value = modalOrganizationTax?.value?.trim() || "";
    if (organizationContactNameInput) organizationContactNameInput.value = modalOrganizationContactName?.value?.trim() || "";
    if (organizationContactEmailInput) organizationContactEmailInput.value = email;
    if (organizationSelect) organizationSelect.value = "";

    renderOrganizationState();
    suggestTitle();
    updateSummary();
    bootstrap.Modal.getOrCreateInstance(organizationModalElement).hide();
  });

  clearNewOrganization?.addEventListener("click", clearOrganizationDraft);
  organizationSelect?.addEventListener("change", () => {
    if (organizationSelect.value) clearOrganizationDraft();
    suggestTitle();
    updateSummary();
  });

  participantModalElement?.addEventListener("show.bs.modal", resetParticipantModal);
  saveNewParticipant?.addEventListener("click", () => {
    const email = modalParticipantEmail?.value?.trim().toLowerCase() || "";
    const password = modalParticipantPassword?.value || "";
    const firstName = modalParticipantFirstName?.value?.trim() || "";
    const lastName = modalParticipantLastName?.value?.trim() || "";

    if (!email || !modalParticipantEmail.checkValidity()) {
      showParticipantError("Ingresa un correo electrónico válido.");
      modalParticipantEmail?.focus();
      return;
    }
    if (existingChecks.some(input => input.closest(".participant-option")?.dataset.email?.toLowerCase() === email)) {
      showParticipantError("Este correo ya existe. Selecciona el usuario en la lista.");
      return;
    }
    if (newParticipants.some(item => item.email === email)) {
      showParticipantError("Este participante ya fue agregado.");
      return;
    }
    if (password.length < 8) {
      showParticipantError("La contraseña temporal debe tener al menos 8 caracteres.");
      modalParticipantPassword?.focus();
      return;
    }
    if (selectedMode() === "INDIVIDUAL" && currentParticipantTotal() >= 1) {
      showParticipantError("Un proceso individual solo puede tener un participante.");
      return;
    }

    newParticipants.push({
      email,
      first_name: firstName,
      last_name: lastName,
      password,
    });
    persistNewParticipants();
    renderSelectedParticipants();
    updateSummary();
    bootstrap.Modal.getOrCreateInstance(participantModalElement).hide();
  });

  generatePassword?.addEventListener("click", () => {
    if (!modalParticipantPassword) return;
    modalParticipantPassword.value = generateSecurePassword();
    modalParticipantPassword.type = "text";
    togglePassword?.querySelector("i")?.classList.replace("bi-eye", "bi-eye-slash");
    modalParticipantPassword.focus();
    modalParticipantPassword.select();
  });

  togglePassword?.addEventListener("click", () => {
    if (!modalParticipantPassword) return;
    const showing = modalParticipantPassword.type === "text";
    modalParticipantPassword.type = showing ? "password" : "text";
    const icon = togglePassword.querySelector("i");
    icon?.classList.toggle("bi-eye", showing);
    icon?.classList.toggle("bi-eye-slash", !showing);
  });

  modeInputs.forEach(input => input.addEventListener("change", () => {
    if (selectedMode() === "INDIVIDUAL" && currentParticipantTotal() > 1) {
      const checked = existingChecks.filter(item => item.checked);
      checked.slice(1).forEach(item => { item.checked = false; });
      if (checked.length > 0) newParticipants = [];
      else if (newParticipants.length > 1) newParticipants = newParticipants.slice(0, 1);
      persistNewParticipants();
      renderSelectedParticipants();
    }
    renderOrganizationState();
    suggestTitle();
    updateSummary();
  }));

  programSelect?.addEventListener("change", () => {
    suggestTitle();
    updateSummary();
  });

  titleInput?.addEventListener("input", () => {
    titleWasEdited = Boolean(titleInput.value.trim());
  });

  assignAssessment?.addEventListener("change", updateSummary);
  existingChecks.forEach(input => input.addEventListener("change", event => {
    if (selectedMode() === "INDIVIDUAL" && event.target.checked) {
      existingChecks.filter(item => item !== event.target).forEach(item => { item.checked = false; });
      newParticipants = [];
      persistNewParticipants();
    }
    renderSelectedParticipants();
    updateSummary();
  }));

  participantSearch?.addEventListener("input", filterParticipants);
  document.addEventListener("keydown", event => {
    if (
      event.key === "/" &&
      document.activeElement?.tagName !== "INPUT" &&
      document.activeElement?.tagName !== "TEXTAREA"
    ) {
      event.preventDefault();
      participantSearch?.focus();
    }
  });

  form.addEventListener("submit", () => {
    persistNewParticipants();
    submitButtons.forEach(button => {
      button.disabled = true;
      button.innerHTML = '<span class="spinner-border spinner-border-sm me-2" aria-hidden="true"></span>Creando...';
    });
  });

  renderOrganizationState();
  renderSelectedParticipants();
  suggestTitle();
  updateSummary();
  filterParticipants();
});