// Pop-up-Fenster: Buttons mit data-open="<dialog-id>" öffnen, data-close schließt.
document.querySelectorAll("[data-open]").forEach((btn) => {
  btn.addEventListener("click", () => document.getElementById(btn.dataset.open).showModal());
});
document.querySelectorAll("dialog").forEach((dialog) => {
  dialog.addEventListener("click", (e) => { if (e.target === dialog) dialog.close(); }); // Klick daneben
  dialog.querySelectorAll("[data-close]").forEach((b) => b.addEventListener("click", () => dialog.close()));
});

// "Neues Kartenset": Kartenzeilen hinzufügen / entfernen
const rows = document.getElementById("card-rows");
if (rows) {
  const template = document.getElementById("card-row-tpl");
  const renumber = () =>
    rows.querySelectorAll(".row-num").forEach((el, i) => { el.textContent = i + 1; });

  const addRow = () => {
    rows.append(template.content.cloneNode(true));
    renumber();
    rows.lastElementChild.querySelector("textarea").focus();
  };

  document.getElementById("add-row").addEventListener("click", addRow);

  rows.addEventListener("click", (e) => {
    const btn = e.target.closest(".remove-row");
    if (!btn) return;
    const row = btn.closest(".new-card");
    if (rows.children.length > 1) row.remove();
    else row.querySelectorAll("textarea").forEach((t) => { t.value = ""; });
    renumber();
  });

  // Tab im letzten Antwortfeld legt automatisch eine neue Karte an
  rows.addEventListener("keydown", (e) => {
    if (e.key !== "Tab" || e.shiftKey) return;
    const last = rows.lastElementChild;
    if (last && e.target === last.querySelector('textarea[name="answer"]') && e.target.value.trim()) {
      e.preventDefault();
      addRow();
    }
  });
}
