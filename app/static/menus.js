// I menu a tendina della barra: tool aziendali e comandi della sessione.
//
// In note-condivise questo e' un hook React (`useOutsideClick`) montato su
// ogni menu. Qui non c'e' React, e tre listener per tendina sarebbero tre
// volte il lavoro per una barra che ne ha due: un solo listener sul document
// decide chi apre e chi chiude, guardando da dove arriva il click.
//
// Il pannello e' `hidden` finche' non si apre, cosi' senza JavaScript non
// resta a mezz'aria in fondo alla pagina.
(function () {
  "use strict";

  function pannelli() {
    return Array.prototype.slice.call(document.querySelectorAll(".menu-panel"));
  }

  function chiudiTutti(tranne) {
    pannelli().forEach(function (p) {
      if (p === tranne) return;
      p.hidden = true;
      var b = document.querySelector('[data-menu="' + p.id + '"]');
      if (b) b.setAttribute("aria-expanded", "false");
    });
  }

  document.addEventListener("click", function (e) {
    var bottone = e.target.closest ? e.target.closest("[data-menu]") : null;

    if (bottone) {
      var p = document.getElementById(bottone.getAttribute("data-menu"));
      if (!p) return;
      var apri = p.hidden;
      chiudiTutti(p);
      p.hidden = !apri;
      bottone.setAttribute("aria-expanded", apri ? "true" : "false");
      return;
    }

    // Un click dentro un pannello aperto lo lascia aperto solo se non e' un
    // comando: un link o un bottone porta altrove, e la tendina che resta
    // aperta sopra la pagina nuova sembra un errore di disegno.
    var dentro = e.target.closest ? e.target.closest(".menu-panel") : null;
    if (dentro && !e.target.closest("a, button")) return;

    chiudiTutti(null);
  });

  // Escape chiude, ed e' l'unica via d'uscita da tastiera: senza, chi non usa
  // il mouse resta con la tendina aperta e deve entrarci dentro per uscirne.
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") chiudiTutti(null);
  });
})();
