document.addEventListener("DOMContentLoaded", () => {
  const input = document.getElementById("users-search");
  const rows = [...document.querySelectorAll("[data-user-row]")];
  const empty = document.getElementById("users-empty-search");
  if (!input || rows.length === 0) return;

  const filter = () => {
    const query = input.value.trim().toLowerCase();
    let visible = 0;
    rows.forEach(row => {
      const matches = !query || row.dataset.search.includes(query);
      row.style.display = matches ? "" : "none";
      if (matches) visible += 1;
    });
    empty?.classList.toggle("d-none", visible !== 0 || !query);
  };

  input.addEventListener("input", filter);
});