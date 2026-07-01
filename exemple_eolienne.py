"""Exemple d'utilisation du cœur générique : une éolienne simplifiée.

Trois composants sont désormais entièrement modélisés et servent de MODÈLES :
    - Rotor        : convertit le vent en puissance (courbe de puissance) ;
    - Generatrice  : convertit cette puissance en électricité (U, I, T°) ;
    - Multiplicateur : température d'huile avec inertie thermique.
Le reste (roulements, autres anomalies...) est balisé « TODO » et reste à
écrire par votre équipe, sur le même patron. C'est la partie « métier » du
projet, celle que vous êtes notés à concevoir et à défendre.

Le module `noyau` ne connaît rien de l'éolien : toute la connaissance du
système vit ici, dans des sous-classes. Modéliser un autre système reviendrait
à écrire un fichier équivalent, sans toucher au noyau.
"""
from __future__ import annotations

import math
import random

from noyau import (Anomalie, Capteur, Composant, Exportateur,
                   Mesures, MoteurSimulation, Scenario, Systeme)


# ---------------------------------------------------------------------------
# Capteurs concrets
# ---------------------------------------------------------------------------
class CapteurEtat(Capteur):
    """Capteur qui lit une grandeur nommée de l'état du composant."""

    def __init__(self, nom: str, unite: str, grandeur: str,
                 bruit: float = 0.0) -> None:
        super().__init__(nom, unite, bruit)
        self.grandeur = grandeur

    def _valeur_brute(self, composant, t, contexte) -> float:
        return composant.etat.get(self.grandeur, 0.0)


class CapteurContexte(Capteur):
    """Capteur qui lit une grandeur du contexte (ex : l'anémomètre lit le vent)."""

    def __init__(self, nom: str, unite: str, grandeur: str,
                 bruit: float = 0.0) -> None:
        super().__init__(nom, unite, bruit)
        self.grandeur = grandeur

    def _valeur_brute(self, composant, t, contexte) -> float:
        return contexte.get(self.grandeur, 0.0)


# ---------------------------------------------------------------------------
# Composants concrets
# ---------------------------------------------------------------------------
class Rotor(Composant):
    """Rotor de l'éolienne : convertit le vent en puissance.

    Applique les régimes de la courbe de puissance : arrêt sous 3 m/s, montée
    en cube du vent jusqu'au nominal, plateau plafonné par la régulation, puis
    arrêt de sécurité au-delà de la vitesse de coupure.
    """

    RAYON = 40.0          # m  (longueur de pale)
    CP = 0.4              # rendement (coefficient de puissance, < 0.593)
    VENT_DEMARRAGE = 3.0  # m/s
    VENT_NOMINAL = 12.0   # m/s
    VENT_COUPURE = 25.0   # m/s

    def _actualiser_etat(self, t: float, contexte: Mesures) -> None:
        vent = contexte.get("vent", 0.0)
        rho = contexte.get("densite_air", 1.225)
        surface = math.pi * self.RAYON ** 2

        if vent < self.VENT_DEMARRAGE or vent > self.VENT_COUPURE:
            puissance_w = 0.0
        elif vent <= self.VENT_NOMINAL:
            puissance_w = 0.5 * rho * surface * self.CP * vent ** 3
        else:  # au-dessus du nominal : régulation -> puissance plafonnée
            puissance_w = 0.5 * rho * surface * self.CP * self.VENT_NOMINAL ** 3

        self.etat["puissance"] = puissance_w / 1000.0            # kW
        self.etat["temperature"] = 20.0 + 0.02 * self.etat["puissance"]

        # On dépose la puissance dans le contexte : la génératrice, mise à jour
        # juste après, pourra la relire (le contexte sert de « bus » du pas).
        contexte["puissance_rotor"] = self.etat["puissance"]
        # TODO: vitesse de rotation (tr/min), corrélée au vent jusqu'au nominal
        # TODO: angle des pales (pitch) : ~0° sous le nominal, augmente au-dessus


class Generatrice(Composant):
    """Convertit la puissance mécanique du rotor en électricité.

    Modèle simplifié : tension régulée à une valeur constante en charge,
    courant déduit de la relation P = U * I, et échauffement du bobinage
    proportionnel au carré du courant (pertes par effet Joule).
    """

    TENSION_NOMINALE = 690.0  # V
    COEFF_ECHAUFFEMENT = 4e-6  # °C par ampère²

    def _actualiser_etat(self, t: float, contexte: Mesures) -> None:
        puissance_w = contexte.get("puissance_rotor", 0.0) * 1000.0  # kW -> W
        temperature_ambiante = contexte.get("temperature_ambiante", 20.0)

        if puissance_w <= 0.0:  # à l'arrêt : pas de production
            self.etat["tension"] = 0.0
            self.etat["courant"] = 0.0
            self.etat["temperature"] = temperature_ambiante
        else:
            self.etat["tension"] = self.TENSION_NOMINALE
            self.etat["courant"] = puissance_w / self.TENSION_NOMINALE
            self.etat["temperature"] = (
                temperature_ambiante
                + self.COEFF_ECHAUFFEMENT * self.etat["courant"] ** 2)


class Multiplicateur(Composant):
    """Boîte de vitesses : élève la vitesse du rotor vers la génératrice.

    On modélise sa température d'huile, qui monte avec la charge mais AVEC DE
    L'INERTIE : elle ne saute pas d'un coup, elle tend progressivement vers une
    température d'équilibre. Ce composant se SOUVIENT donc de sa température
    d'un pas au suivant (contrairement au rotor et à la génératrice, dont la
    sortie ne dépend que de l'instant présent).
    """

    INERTIE = 0.05               # 0 = très lent à réagir, 1 = instantané
    ECHAUFFEMENT_MAX = 45.0      # °C au-dessus de l'ambiant à pleine charge
    PUISSANCE_NOMINALE = 2000.0  # kW, charge de référence

    def _actualiser_etat(self, t: float, contexte: Mesures) -> None:
        puissance = contexte.get("puissance_rotor", 0.0)
        ambiante = contexte.get("temperature_ambiante", 20.0)

        # Température d'équilibre visée, selon la charge du moment (0 à ~1).
        charge = puissance / self.PUISSANCE_NOMINALE
        temperature_cible = ambiante + self.ECHAUFFEMENT_MAX * charge

        # Au tout premier pas, on démarre à la température ambiante.
        temperature_actuelle = self.etat.get("temperature_huile", ambiante)

        # Inertie : on ne comble qu'une fraction de l'écart à la cible par pas.
        self.etat["temperature_huile"] = temperature_actuelle + self.INERTIE * (
            temperature_cible - temperature_actuelle)


# TODO: class Roulement(Composant): T°, vibration...


# ---------------------------------------------------------------------------
# Scénario d'environnement
# ---------------------------------------------------------------------------
class ScenarioVent(Scenario):
    """Scénario simple : le vent oscille doucement autour d'une moyenne."""

    def __init__(self, vent_moyen: float = 10.0) -> None:
        self.vent_moyen = vent_moyen

    def contexte(self, t: float) -> Mesures:
        vent = self.vent_moyen + 1.5 * math.sin(t / 30.0) + random.gauss(0, 0.1)
        vent = max(0.0, vent)
        # TODO: faire varier température ambiante et pression au cours du temps,
        #       puis en déduire la densité de l'air : rho = p / (R * T).
        return {
            "vent": vent,
            "densite_air": 1.225,
            "temperature_ambiante": 20.0,
        }


# ---------------------------------------------------------------------------
# Anomalie concrète  (EXEMPLE : dérive d'une grandeur d'un composant)
# ---------------------------------------------------------------------------
class DeriveGrandeur(Anomalie):
    """Dérive linéaire d'une grandeur d'un composant à partir de `instant_debut`.

    À chaque pas, on ajoute `pente * (t - instant_debut)` à la grandeur visée :
      - une pente POSITIVE modélise une surchauffe (une température qui monte) ;
      - une pente NÉGATIVE modélise une chute (ex : une perte de puissance).
    Dans les deux cas, la grandeur s'écarte de son comportement normal alors que
    le reste est inchangé : c'est cette rupture de corrélation que l'IA de la
    partie 2 apprendra à repérer.

    ATTENTION : à réserver aux grandeurs RECALCULÉES à chaque pas (température du
    rotor, puissance, tension...). Sur une grandeur à mémoire/inertie (la T°
    d'huile du multiplicateur, qui relit sa valeur précédente), l'écart se
    ré-injecterait à chaque pas et s'amplifierait. Pour un tel composant, il
    faudrait plutôt faire monter sa température CIBLE, pas sa valeur courante.
    """

    def __init__(self, nom: str, instant_debut: float, nom_composant: str,
                 grandeur: str, pente: float) -> None:
        super().__init__(nom, instant_debut)
        self.nom_composant = nom_composant
        self.grandeur = grandeur
        self.pente = pente  # dérive ajoutée par unité de temps

    def appliquer(self, systeme: Systeme, t: float, contexte: Mesures) -> None:
        ecart = self.pente * (t - self.instant_debut)
        for composant in systeme.composants:
            if composant.nom == self.nom_composant:
                base = composant.etat.get(self.grandeur, 0.0)
                composant.etat[self.grandeur] = base + ecart
        # TODO: autres anomalies -> panne du pitch (surtension), balourd
        #       (vibration), désalignement yaw, dégradation progressive...


# ---------------------------------------------------------------------------
# Assemblage et démonstration
# ---------------------------------------------------------------------------
def construire_eolienne() -> Systeme:
    """Construit une éolienne AVEC le logiciel générique (rotor, génératrice, multiplicateur)."""
    eolienne = Systeme("eolienne")

    # Le rotor est ajouté EN PREMIER : il dépose sa puissance dans le contexte,
    # que la génératrice relit ensuite. L'ordre d'ajout compte donc.
    rotor = Rotor("rotor")
    rotor.ajouter_capteur(CapteurContexte("anemometre", "m/s", "vent", bruit=0.2))
    rotor.ajouter_capteur(CapteurEtat("puissance", "kW", "puissance", bruit=2.0))
    rotor.ajouter_capteur(CapteurEtat("temperature", "degC", "temperature",
                                      bruit=0.3))
    eolienne.ajouter_composant(rotor)

    generatrice = Generatrice("generatrice")
    generatrice.ajouter_capteur(CapteurEtat("tension", "V", "tension", bruit=1.0))
    generatrice.ajouter_capteur(CapteurEtat("courant", "A", "courant", bruit=2.0))
    generatrice.ajouter_capteur(CapteurEtat("temperature", "degC",
                                            "temperature", bruit=0.3))
    eolienne.ajouter_composant(generatrice)

    multiplicateur = Multiplicateur("multiplicateur")
    multiplicateur.ajouter_capteur(CapteurEtat("temperature_huile", "degC",
                                               "temperature_huile", bruit=0.3))
    eolienne.ajouter_composant(multiplicateur)

    # TODO: ajouter Roulement... et leurs capteurs.
    return eolienne


if __name__ == "__main__":
    # 1) Jeu NOMINAL (sans anomalie) : sert à ENTRAÎNER le modèle d'IA.
    moteur = MoteurSimulation(construire_eolienne(),
                              ScenarioVent(vent_moyen=10.0), pas_temps=1.0)
    donnees_nominales = moteur.executer(duree=120)
    Exportateur.vers_csv(donnees_nominales, "donnees_nominales.csv")

    # 2) Jeu AVEC ANOMALIE : sert à TESTER le modèle d'IA.
    moteur_test = MoteurSimulation(construire_eolienne(),
                                   ScenarioVent(vent_moyen=10.0), pas_temps=1.0)
    moteur_test.injecter(DeriveGrandeur(
        nom="surchauffe_rotor", instant_debut=60, nom_composant="rotor",
        grandeur="temperature", pente=0.5))
    donnees_anomalie = moteur_test.executer(duree=120)
    Exportateur.vers_csv(donnees_anomalie, "donnees_avec_anomalie.csv")

    print("Deux jeux de données générés : nominal + anomalie.")
