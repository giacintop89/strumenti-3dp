# Strumenti 3DP

Repository per gli strumenti della suite dedicati alla stampa 3D. Non è
ancora stato deciso quale strumento ospiterà per primo: per ora contiene solo
il guscio comune (accesso, utenti, menu della suite), clonato da
[strumenti-cnc](https://github.com/giacintop89/strumenti-cnc) — stessa
struttura, stessi pattern, senza nulla di specifico al CNC.

Uno strumento va aggiunto come suo pacchetto sotto `app/core/` con un router
proprio, seguendo lo schema che `strumenti-cnc` usa per G-code e SVG.
