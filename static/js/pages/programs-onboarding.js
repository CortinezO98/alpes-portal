document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("engagement-onboarding-form");
  if (!form) return;

  const modeInputs = [...form.querySelectorAll('input[name="mode"]')];
  const orgSection = document.getElementById("organization-section");
  const orgExistingWrap = document.getElementById("organization-existing-wrap");
  const createOrg = document.getElementById("id_create_organization");
  const quickOrg = document.getElementById("organization-quick-create");
  const orgSelect = document.getElementById("id_organization");
  const orgName = document.getElementById("id_organization_name");
  const programSelect = document.getElementById("id_program");
  const assignAssessment = document.getElementById("id_assign_assessment");
  const assessmentWrap = document.getElementById("assessment-template-wrap");
  const participantSearch = document.getElementById("participant-search");
  const participantOptions = [...document.querySelectorAll(".participant-option")];
  const existingChecks = [...document.querySelectorAll(".participant-existing-check")];
  const addParticipant = document.getElementById("add-new-participant");
  const newParticipantList = document.getElementById("new-participants-list");
  const hiddenParticipants = document.getElementById("id_new_participants_json");
  const counter = document.getElementById("participant-count");

  const summaryMode = document.getElementById("summary-mode");
  const summaryOrganization = document.getElementById("summary-organization");
  const summaryProgram = document.getElementById("summary-program");
  const summaryParticipants = document.getElementById("summary-participants");
  const summaryAssessment = document.getElementById("summary-assessment");

  let rowIndex = 0;

  function selectedMode() {
    return modeInputs.find(input => input.checked)?.value || "ORGANIZATIONAL";
  }

  function updateOrganizationState() {
    const organizational = selectedMode() === "ORGANIZATIONAL";
    orgSection.classList.toggle("is-hidden", !organizational);
    if (!organizational) {
      if (orgSelect) orgSelect.value = "";
      if (createOrg) createOrg.checked = false;
    }
    const creating = organizational && createOrg?.checked;
    quickOrg.hidden = !creating;
    orgExistingWrap.classList.toggle("is-hidden", !!creating);
    updateSummary();
  }

  function serializeNewParticipants() {
    const rows = [...newParticipantList.querySelectorAll(".new-participant-card")].map(card => ({
      first_name: card.querySelector('[data-field="first_name"]').value.trim(),
      last_name: card.querySelector('[data-field="last_name"]').value.trim(),
      email: card.querySelector('[data-field="email"]').value.trim(),
      password: card.querySelector('[data-field="password"]').value
    })).filter(row => row.first_name || row.last_name || row.email || row.password);
    hiddenParticipants.value = JSON.stringify(rows);
    return rows;
  }

  function participantTotal() {
    return existingChecks.filter(input => input.checked).length + serializeNewParticipants().length;
  }

  function updateSummary() {
    const modeLabel = selectedMode() === "ORGANIZATIONAL" ? "Empresarial" : "Individual";
    summaryMode.textContent = modeLabel;

    if (selectedMode() === "INDIVIDUAL") {
      summaryOrganization.textContent = "No aplica";
    } else if (createOrg?.checked) {
      summaryOrganization.textContent = orgName?.value.trim() || "Empresa nueva";
    } else {
      summaryOrganization.textContent = orgSelect?.selectedOptions[0]?.text || "Por seleccionar";
      if (!orgSelect?.value) summaryOrganization.textContent = "Por seleccionar";
    }

    summaryProgram.textContent = programSelect?.selectedOptions[0]?.text || "Por seleccionar";
    const total = participantTotal();
    summaryParticipants.textContent = String(total);
    counter.textContent = total === 1 ? "1 seleccionado" : `${total} seleccionados`;
    summaryAssessment.textContent = assignAssessment?.checked ? "Automática" : "Sin asignar";
  }

  function addNewParticipantRow(values = {}) {
    rowIndex += 1;
    const card = document.createElement("div");
    card.className = "new-participant-card";
    card.innerHTML = `
      <button type="button" class="new-participant-remove" aria-label="Eliminar participante">×</button>
      <div class="row g-2 pe-4">
        <div class="col-md-3">
          <label class="form-label small">Nombre</label>
          <input class="form-control form-control-sm" data-field="first_name" value="${values.first_name || ""}" placeholder="Nombre">
        </div>
        <div class="col-md-3">
          <label class="form-label small">Apellido</label>
          <input class="form-control form-control-sm" data-field="last_name" value="${values.last_name || ""}" placeholder="Apellido">
        </div>
        <div class="col-md-4">
          <label class="form-label small">Correo *</label>
          <input type="email" class="form-control form-control-sm" data-field="email" value="${values.email || ""}" placeholder="persona@empresa.com">
        </div>
        <div class="col-md-2">
          <label class="form-label small">Clave temporal *</label>
          <input type="password" class="form-control form-control-sm" data-field="password" value="${values.password || ""}" placeholder="8+ caracteres">
        </div>
      </div>`;
    card.querySelector(".new-participant-remove").addEventListener("click", () => {
      card.remove();
      updateSummary();
    });
    card.querySelectorAll("input").forEach(input => input.addEventListener("input", updateSummary));
    newParticipantList.appendChild(card);
    updateSummary();
  }

  if (hiddenParticipants?.value) {
    try {
      const initialRows = JSON.parse(hiddenParticipants.value);
      initialRows.forEach(row => addNewParticipantRow(row));
    } catch (_) {}
  }

  modeInputs.forEach(input => input.addEventListener("change", updateOrganizationState));
  createOrg?.addEventListener("change", updateOrganizationState);
  orgSelect?.addEventListener("change", updateSummary);
  orgName?.addEventListener("input", updateSummary);
  programSelect?.addEventListener("change", updateSummary);
  assignAssessment?.addEventListener("change", () => {
    assessmentWrap.classList.toggle("is-hidden", !assignAssessment.checked);
    updateSummary();
  });
  existingChecks.forEach(input => input.addEventListener("change", updateSummary));

  participantSearch?.addEventListener("input", event => {
    const query = event.target.value.trim().toLowerCase();
    participantOptions.forEach(option => {
      option.classList.toggle("is-hidden", query && !option.dataset.search.includes(query));
    });
  });

  addParticipant?.addEventListener("click", () => addNewParticipantRow());

  form.addEventListener("submit", event => {
    serializeNewParticipants();
    const submit = form.querySelector(".onboarding-submit");
    if (submit) {
      submit.disabled = true;
      submit.innerHTML = '<span class="spinner-border spinner-border-sm me-2" aria-hidden="true"></span>Creando proceso...';
    }
  });

  updateOrganizationState();
  if (assignAssessment) assessmentWrap.classList.toggle("is-hidden", !assignAssessment.checked);
  updateSummary();
});