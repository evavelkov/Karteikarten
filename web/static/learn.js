// Lernmodus: "Gewusst" nimmt die Karte aus dem Stapel,
// "Nochmal" schiebt sie ans Ende. Fertig, wenn der Stapel leer ist.
(() => {
  const $ = (id) => document.getElementById(id);
  const flip = $("flip");
  let queue, total, attempts, revealed;

  function shuffle(arr) {
    for (let i = arr.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [arr[i], arr[j]] = [arr[j], arr[i]];
    }
    return arr;
  }

  function start(mix) {
    queue = window.CARDS.slice();
    if (mix) shuffle(queue);
    total = queue.length;
    attempts = 0;
    $("stage").hidden = false;
    $("done").hidden = true;
    show();
  }

  function show() {
    const done = total - queue.length;
    $("progress-fill").style.width = `${(done / total) * 100}%`;
    $("progress-text").textContent = `${done} / ${total}`;

    if (!queue.length) {
      $("stage").hidden = true;
      $("done").hidden = false;
      const extra = attempts - total;
      $("done-text").textContent =
        extra === 0
          ? `Alle ${total} Karten auf Anhieb gewusst!`
          : `${total} Karten gelernt, ${extra}× wiederholt.`;
      return;
    }

    const card = queue[0];
    const reverse = $("reverse").checked;
    revealed = false;
    flip.classList.remove("flipped");
    // Inhalt erst nach dem Zurückdrehen tauschen, damit die Antwort nicht aufblitzt
    setTimeout(() => {
      $("front").textContent = reverse ? card.answer : card.question;
      $("back").textContent = reverse ? card.question : card.answer;
    }, flip.dataset.started ? 150 : 0);
    flip.dataset.started = "1";
  }

  function turn() {
    revealed = !revealed;
    flip.classList.toggle("flipped", revealed);
  }

  function grade(known) {
    if (!queue.length) return;
    if (!revealed) return turn(); // erst umdrehen, dann bewerten
    attempts++;
    const card = queue.shift();
    if (!known) queue.push(card);
    show();
  }

  flip.addEventListener("click", turn);
  $("known").addEventListener("click", () => grade(true));
  $("again").addEventListener("click", () => grade(false));
  $("shuffle").addEventListener("click", () => start(true));
  $("restart").addEventListener("click", () => start(false));
  $("reverse").addEventListener("change", show);

  document.addEventListener("keydown", (e) => {
    if (e.target.matches("input, textarea")) return;
    if (e.code === "Space" || e.code === "Enter") { e.preventDefault(); turn(); }
    else if (e.key === "1" || e.key === "ArrowLeft") grade(false);
    else if (e.key === "2" || e.key === "ArrowRight") grade(true);
  });

  start(false);
})();
