document.addEventListener("DOMContentLoaded", () => {
  const search = document.getElementById("engagement-participant-search");
  const status = document.getElementById("engagement-status-filter");
  const rows = [...document.querySelectorAll("[data-engagement-participant-row]")];
  const empty = document.getElementById("engagement-matrix-empty");

  if (!rows.length) return;

  const applyFilters = () => {
    const query = (search?.value || "").trim().toLowerCase();
    const selectedStatus = status?.value || "";
    let visible = 0;

    rows.forEach(row => {
      const matchesSearch = !query || (row.dataset.search || "").includes(query);
      let matchesStatus = true;

      if (selectedStatus === "review") {
        matchesStatus = (row.dataset.review || "").includes("1");
      } else if (selectedStatus === "reopened") {
        matchesStatus = (row.dataset.reopened || "").includes("1");
      } else if (selectedStatus === "completed") {
        matchesStatus = row.dataset.completed === "1";
      }

      const show = matchesSearch && matchesStatus;
      row.hidden = !show;
      if (show) visible += 1;
    });

    empty?.classList.toggle("d-none", visible !== 0);
  };

  search?.addEventListener("input", applyFilters);
  status?.addEventListener("change", applyFilters);
});