"""Tests unitaires de l'exemple éolienne.

Ce fichier sert de MODÈLE : il montre comment tester un composant. Dupliquez
ce patron pour couvrir les autres composants et les anomalies.

Lancement (depuis la racine du projet) :  pytest
"""
from exemple_eolienne import Rotor


def _contexte(vent: float, densite_air: float = 1.225) -> dict:
    """Petit utilitaire : fabrique un contexte environnemental minimal."""
    return {"vent": vent, "densite_air": densite_air}


def test_puissance_nulle_sous_le_demarrage():
    """Sous 3 m/s, l'éolienne ne démarre pas : puissance nulle."""
    rotor = Rotor("rotor")
    rotor.mettre_a_jour(0.0, _contexte(vent=2.0))
    assert rotor.etat["puissance"] == 0.0


def test_puissance_nulle_au_dessus_de_la_coupure():
    """Au-delà de 25 m/s, arrêt de sécurité : puissance nulle."""
    rotor = Rotor("rotor")
    rotor.mettre_a_jour(0.0, _contexte(vent=30.0))
    assert rotor.etat["puissance"] == 0.0


def test_puissance_croit_avec_le_vent_avant_le_nominal():
    """Entre le démarrage et le nominal, plus de vent = plus de puissance."""
    rotor = Rotor("rotor")
    rotor.mettre_a_jour(0.0, _contexte(vent=5.0))
    puissance_faible = rotor.etat["puissance"]
    rotor.mettre_a_jour(0.0, _contexte(vent=9.0))
    puissance_forte = rotor.etat["puissance"]
    assert puissance_forte > puissance_faible


def test_puissance_plafonnee_au_dessus_du_nominal():
    """Au-dessus de 12 m/s, la régulation plafonne la puissance (plateau)."""
    rotor = Rotor("rotor")
    rotor.mettre_a_jour(0.0, _contexte(vent=13.0))
    puissance_13 = rotor.etat["puissance"]
    rotor.mettre_a_jour(0.0, _contexte(vent=20.0))
    puissance_20 = rotor.etat["puissance"]
    assert puissance_13 == puissance_20
