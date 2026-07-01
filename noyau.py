"""Cœur générique du générateur de données pour la maintenance prédictive.

Ce module ne connaît AUCUN système technique en particulier (éolienne, pompe,
moteur de fusée...). Il ne fournit que les briques réutilisables :

    Composant  -- élément d'un système (patron Composite)
    Capteur    -- transforme l'état d'un composant en mesure numérique
    Anomalie   -- perturbation « maîtrisée » injectée dans la simulation
    Scenario   -- conditions d'environnement au cours du temps
    Systeme    -- arbre de composants (racine du Composite)
    MoteurSimulation -- déroule la simulation et produit le jeu de données
    Exportateur      -- écrit le jeu de données au format CSV

Les systèmes concrets sont définis AILLEURS, en héritant de ces classes.
C'est ce qui garantit la généricité exigée par le sujet : le jour où l'on
modélise un autre système, on n'ajoute que de nouvelles sous-classes, sans
jamais toucher à ce fichier.
"""
from __future__ import annotations

import csv
import random
from abc import ABC, abstractmethod
from typing import Dict, List

# Un relevé = un dictionnaire {nom_de_grandeur: valeur}.
Mesures = Dict[str, float]


class Capteur(ABC):
    """Capteur générique posé sur un composant.

    Un capteur lit l'état physique d'un composant (ou le contexte) et en
    produit une mesure numérique, éventuellement bruitée pour imiter un
    capteur réel.
    """

    def __init__(self, nom: str, unite: str, bruit: float = 0.0) -> None:
        self.nom = nom
        self.unite = unite
        self.bruit = bruit  # écart-type du bruit gaussien de mesure

    @abstractmethod
    def _valeur_brute(self, composant: "Composant", t: float,
                      contexte: Mesures) -> float:
        """Valeur idéale mesurée, sans bruit.

        À implémenter par chaque sous-classe de capteur.
        """

    def mesurer(self, composant: "Composant", t: float,
                contexte: Mesures) -> float:
        """Retourne la mesure finale : valeur brute + bruit de mesure."""
        valeur = self._valeur_brute(composant, t, contexte)
        if self.bruit:
            valeur += random.gauss(0.0, self.bruit)
        return valeur


class Composant(ABC):
    """Élément d'un système technique (patron Composite).

    Un composant possède un état physique (`etat`), peut contenir des
    sous-composants et porter des capteurs.
    """

    def __init__(self, nom: str) -> None:
        self.nom = nom
        self.etat: Mesures = {}
        self.capteurs: List[Capteur] = []
        self.sous_composants: List["Composant"] = []

    def ajouter_capteur(self, capteur: Capteur) -> None:
        """Pose un capteur sur ce composant."""
        self.capteurs.append(capteur)

    def ajouter_sous_composant(self, composant: "Composant") -> None:
        """Rattache un sous-composant (ex : un roulement dans une génératrice)."""
        self.sous_composants.append(composant)

    @abstractmethod
    def _actualiser_etat(self, t: float, contexte: Mesures) -> None:
        """Fait évoluer l'état PROPRE du composant à l'instant t.

        C'est ICI que vit la physique du système concret. À implémenter dans
        chaque composant (Rotor, Génératrice, Roulement...).
        """

    def mettre_a_jour(self, t: float, contexte: Mesures) -> None:
        """Actualise ce composant, puis ses sous-composants (générique)."""
        self._actualiser_etat(t, contexte)
        for enfant in self.sous_composants:
            enfant.mettre_a_jour(t, contexte)

    def relever(self, t: float, contexte: Mesures) -> Mesures:
        """Relève toutes les mesures de ce composant et de ses sous-composants."""
        mesures: Mesures = {}
        for capteur in self.capteurs:
            cle = f"{self.nom}.{capteur.nom}"
            mesures[cle] = capteur.mesurer(self, t, contexte)
        for enfant in self.sous_composants:
            mesures.update(enfant.relever(t, contexte))
        return mesures


class Systeme:
    """Système technique complet : la racine de l'arbre de composants."""

    def __init__(self, nom: str) -> None:
        self.nom = nom
        self.composants: List[Composant] = []

    def ajouter_composant(self, composant: Composant) -> None:
        """Ajoute un composant de premier niveau au système."""
        self.composants.append(composant)

    def mettre_a_jour(self, t: float, contexte: Mesures) -> None:
        """Fait évoluer tout le système d'un pas de temps."""
        for composant in self.composants:
            composant.mettre_a_jour(t, contexte)

    def relever(self, t: float, contexte: Mesures) -> Mesures:
        """Agrège les mesures de tous les composants en un seul relevé."""
        mesures: Mesures = {}
        for composant in self.composants:
            mesures.update(composant.relever(t, contexte))
        return mesures


class Anomalie(ABC):
    """Perturbation « maîtrisée » injectée dans une simulation.

    Une anomalie devient active à partir de `instant_debut` et modifie l'état
    d'un composant (ou une mesure) de façon contrôlée, afin de tester ensuite
    la capacité d'un modèle d'IA à la détecter.
    """

    def __init__(self, nom: str, instant_debut: float,
                 intensite: float = 1.0) -> None:
        self.nom = nom
        self.instant_debut = instant_debut
        self.intensite = intensite

    def est_active(self, t: float) -> bool:
        """Indique si l'anomalie doit s'appliquer à l'instant t."""
        return t >= self.instant_debut

    @abstractmethod
    def appliquer(self, systeme: Systeme, t: float, contexte: Mesures) -> None:
        """Applique la perturbation. À implémenter par chaque sous-classe."""


class Scenario(ABC):
    """Fournit les conditions d'environnement au cours du temps.

    Pour une éolienne : vitesse du vent, température ambiante, pression...
    """

    @abstractmethod
    def contexte(self, t: float) -> Mesures:
        """Retourne le contexte environnemental à l'instant t."""


class MoteurSimulation:
    """Chef d'orchestre : déroule la simulation et produit le jeu de données.

    À chaque pas de temps :
        1. lit le contexte auprès du scénario ;
        2. fait évoluer le système (physique nominale) ;
        3. applique les anomalies actives ;
        4. relève tous les capteurs.
    """

    def __init__(self, systeme: Systeme, scenario: Scenario,
                 pas_temps: float = 1.0) -> None:
        self.systeme = systeme
        self.scenario = scenario
        self.pas_temps = pas_temps
        self.anomalies: List[Anomalie] = []

    def injecter(self, anomalie: Anomalie) -> None:
        """Enregistre une anomalie à faire jouer pendant la simulation."""
        self.anomalies.append(anomalie)

    def executer(self, duree: float) -> List[Mesures]:
        """Simule le système de 0 à `duree` et renvoie la liste des relevés."""
        lignes: List[Mesures] = []
        nb_pas = int(duree / self.pas_temps) + 1
        for i in range(nb_pas):
            t = i * self.pas_temps
            contexte = self.scenario.contexte(t)
            self.systeme.mettre_a_jour(t, contexte)
            for anomalie in self.anomalies:
                if anomalie.est_active(t):
                    anomalie.appliquer(self.systeme, t, contexte)
            ligne: Mesures = {"temps": t}
            ligne.update(self.systeme.relever(t, contexte))
            lignes.append(ligne)
        return lignes


class Exportateur:
    """Exporte un jeu de données vers un fichier CSV."""

    @staticmethod
    def vers_csv(lignes: List[Mesures], chemin: str) -> None:
        """Écrit les relevés dans un fichier CSV (en-tête + une ligne par pas)."""
        if not lignes:
            raise ValueError("Aucune donnée à exporter.")
        colonnes = list(lignes[0].keys())
        with open(chemin, "w", newline="", encoding="utf-8") as fichier:
            ecrivain = csv.DictWriter(fichier, fieldnames=colonnes)
            ecrivain.writeheader()
            ecrivain.writerows(lignes)
