"""IHM de démonstration (point de départ à enrichir).

Fenêtre Tkinter qui visualise l'éolienne :
  - à gauche, une vue 2D dont le rotor tourne à une vitesse liée à la puissance ;
  - à droite, plusieurs graphes empilés (un par échelle de grandeur).
Une liste déroulante permet de choisir un SCÉNARIO (nominal ou différentes
anomalies), puis de le rejouer.

Deux tables de configuration pilotent l'IHM :
  - GRAPHES   : quels capteurs afficher, et sur quel graphe ;
  - SCENARIOS : quelles anomalies injecter pour chaque scénario.
Ajouter un graphe ou un scénario = ajouter une entrée, sans toucher au reste.

L'IHM ne recalcule rien : elle rejoue un jeu de données produit par le moteur
générique. Le calcul reste dans le noyau, l'affichage reste dans l'IHM.

⚠️ SQUELETTE D'IHM, à rendre ergonomique/esthétique et à internationaliser
(FR/EN). C'est un livrable noté : soignez-le vous-mêmes.

Dépendance :  pip install matplotlib
"""
from __future__ import annotations

import math
import tkinter as tk
from tkinter import ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from exemple_eolienne import (DeriveGrandeur, ScenarioVent,
                              construire_eolienne)
from noyau import MoteurSimulation

DUREE = 120          # nombre de pas simulés
INTERVALLE_MS = 60   # délai entre deux images de l'animation
DEBUT_ANOMALIE = 60  # instant de déclenchement des anomalies

# Graphes : (titre, unité, [(légende, clé_capteur, couleur), ...]).
GRAPHES = [
    ("Puissance", "kW", [("puissance", "rotor.puissance", "#1f77b4")]),
    ("Tension", "V", [("tension", "generatrice.tension", "#ff7f0e")]),
    ("Températures", "°C", [
        ("T° rotor", "rotor.temperature", "green"),
        ("T° huile", "multiplicateur.temperature_huile", "red"),
    ]),
]

# Scénarios : nom -> liste d'anomalies à injecter (vide = fonctionnement normal).
# Une même classe (DeriveGrandeur) produit des anomalies très différentes selon
# le composant visé et le signe de la pente.
SCENARIOS = {
    "Nominal": [],
    "Surchauffe du rotor": [
        DeriveGrandeur("surchauffe_rotor", DEBUT_ANOMALIE,
                       "rotor", "temperature", pente=0.5)],
    "Surtension (génératrice)": [
        DeriveGrandeur("surtension", DEBUT_ANOMALIE,
                       "generatrice", "tension", pente=1.5)],
    "Chute de puissance": [
        DeriveGrandeur("chute_puissance", DEBUT_ANOMALIE,
                       "rotor", "puissance", pente=-8.0)],
}


class ApplicationEolienne(tk.Tk):
    """Fenêtre principale de l'IHM de démonstration."""

    def __init__(self) -> None:
        super().__init__()
        self.title("GADMAPS — Démonstration éolienne")
        self.geometry("980x620")

        self.cles = [cle for _, _, series in GRAPHES for (_, cle, _) in series]

        self.donnees: list = []
        self.index = 0
        self.angle = 0.0
        self.nom_scenario = "Nominal"
        self._apres = None

        self._construire_interface()
        self.lancer_scenario_choisi()

    # ------------------------------------------------------------------ #
    #  Construction de l'interface
    # ------------------------------------------------------------------ #
    def _construire_interface(self) -> None:
        barre = ttk.Frame(self, padding=8)
        barre.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(barre, text="Scénario :").pack(side=tk.LEFT, padx=(0, 4))
        self.choix = ttk.Combobox(barre, values=list(SCENARIOS),
                                  state="readonly", width=26)
        self.choix.set("Nominal")
        self.choix.pack(side=tk.LEFT, padx=4)
        ttk.Button(barre, text="Lancer",
                   command=self.lancer_scenario_choisi).pack(side=tk.LEFT, padx=4)

        self.etiquette = ttk.Label(barre, text="")
        self.etiquette.pack(side=tk.LEFT, padx=16)

        corps = ttk.Frame(self)
        corps.pack(fill=tk.BOTH, expand=True)

        # Vue 2D de l'éolienne (à gauche).
        self.canvas = tk.Canvas(corps, width=360, height=540, bg="#eaf1f8",
                                highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=8)

        # Un sous-graphe par entrée de GRAPHES, partageant l'axe du temps.
        self.figure = Figure(figsize=(5, 6), dpi=100)
        self.axes = []
        nb = len(GRAPHES)
        for i in range(nb):
            partage = self.axes[0] if self.axes else None
            self.axes.append(self.figure.add_subplot(nb, 1, i + 1,
                                                     sharex=partage))

        self.trace = FigureCanvasTkAgg(self.figure, master=corps)
        self.trace.get_tk_widget().pack(side=tk.RIGHT, fill=tk.BOTH,
                                        expand=True, padx=8, pady=8)

    # ------------------------------------------------------------------ #
    #  Génération du scénario choisi
    # ------------------------------------------------------------------ #
    def lancer_scenario_choisi(self) -> None:
        """Construit et rejoue le scénario sélectionné dans la liste."""
        nom = self.choix.get()
        moteur = MoteurSimulation(construire_eolienne(),
                                  ScenarioVent(vent_moyen=10.0), pas_temps=1.0)
        for anomalie in SCENARIOS[nom]:
            moteur.injecter(anomalie)
        self._demarrer(moteur.executer(DUREE), nom_scenario=nom)

    def _demarrer(self, donnees: list, nom_scenario: str) -> None:
        """Réinitialise l'animation avec un nouveau jeu de données."""
        if self._apres is not None:
            self.after_cancel(self._apres)
        self.donnees = donnees
        self.index = 0
        self.nom_scenario = nom_scenario
        self.temps: list = []
        self.series: dict = {cle: [] for cle in self.cles}
        self._animer()

    # ------------------------------------------------------------------ #
    #  Boucle d'animation
    # ------------------------------------------------------------------ #
    def _animer(self) -> None:
        if self.index >= len(self.donnees):
            return
        ligne = self.donnees[self.index]

        self.temps.append(ligne["temps"])
        for cle in self.cles:
            self.series[cle].append(ligne[cle])

        puissance = ligne["rotor.puissance"]
        tourne = puissance > 1.0
        if tourne:
            self.angle += 0.06 + puissance / 8000.0
        self._dessiner_eolienne(self.angle, tourne)

        self._tracer_courbes()

        actif = self.nom_scenario != "Nominal" and ligne["temps"] >= DEBUT_ANOMALIE
        etat = self.nom_scenario + (" ▲" if actif else "")
        self.etiquette.config(
            text=f"t={ligne['temps']:.0f}s   "
                 f"vent={ligne['rotor.anemometre']:.1f} m/s   "
                 f"puissance={puissance:.0f} kW   "
                 f"U={ligne['generatrice.tension']:.0f} V   "
                 f"T°rotor={ligne['rotor.temperature']:.0f}   [{etat}]")

        self.index += 1
        self._apres = self.after(INTERVALLE_MS, self._animer)

    def _dessiner_eolienne(self, angle: float, tourne: bool) -> None:
        """Redessine le mât, le moyeu et les trois pales à l'angle courant."""
        c = self.canvas
        c.delete("all")
        cx, cy = 180, 180
        c.create_polygon(170, cy, 190, cy, 200, 520, 160, 520,
                         fill="#cfd8e2", outline="#9fb0c2")
        longueur = 120
        for i in range(3):
            a = angle + i * (2 * math.pi / 3)
            x = cx + longueur * math.cos(a)
            y = cy + longueur * math.sin(a)
            c.create_line(cx, cy, x, y, width=10, fill="#3a5a7d",
                         capstyle=tk.ROUND)
        c.create_oval(cx - 10, cy - 10, cx + 10, cy + 10,
                     fill="#5a6b7d", outline="")
        if not tourne:
            c.create_text(cx, 60, text="ARRÊT", fill="#a32d2d",
                         font=("Sans", 16, "bold"))

    def _tracer_courbes(self) -> None:
        """Redessine chaque graphe à partir de la liste GRAPHES."""
        for axe, (titre, unite, series) in zip(self.axes, GRAPHES):
            axe.clear()
            for legende, cle, couleur in series:
                axe.plot(self.temps, self.series[cle], label=legende,
                         color=couleur)
            axe.set_ylabel(unite)
            axe.set_title(titre, fontsize=9, loc="left")
            axe.legend(loc="upper left", fontsize=8)
            axe.grid(True, alpha=0.3)
        self.axes[-1].set_xlabel("temps (s)")
        self.figure.tight_layout()
        self.trace.draw()


if __name__ == "__main__":
    # TODO: internationalisation (FR/EN) de tous les libellés.
    # TODO: styliser l'IHM (couleurs, disposition, thème).
    ApplicationEolienne().mainloop()
