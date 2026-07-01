"""Tests unitaires du multiplicateur, centrés sur l'inertie thermique.

Lancement (depuis la racine) :  pytest
"""
from exemple_eolienne import Multiplicateur


def _contexte(puissance_rotor: float, temperature_ambiante: float = 20.0) -> dict:
    return {
        "puissance_rotor": puissance_rotor,
        "temperature_ambiante": temperature_ambiante,
    }


def test_huile_ne_saute_pas_a_la_cible_en_un_pas():
    """À pleine charge d'un coup, l'inertie empêche d'atteindre la cible tout de suite."""
    multiplicateur = Multiplicateur("multiplicateur")
    multiplicateur.mettre_a_jour(0.0, _contexte(puissance_rotor=2000.0))
    # La cible serait ~65 °C ; après un seul pas on est encore bien en dessous.
    assert multiplicateur.etat["temperature_huile"] < 30.0


def test_huile_monte_sous_charge_soutenue():
    """Sous charge maintenue, la température grimpe pas après pas."""
    multiplicateur = Multiplicateur("multiplicateur")
    temperatures = []
    for _ in range(50):
        multiplicateur.mettre_a_jour(0.0, _contexte(puissance_rotor=2000.0))
        temperatures.append(multiplicateur.etat["temperature_huile"])
    assert temperatures[-1] > temperatures[0]
    assert temperatures[-1] > 50.0  # elle s'approche de la cible


def test_huile_redescend_quand_la_charge_tombe():
    """Sans charge, la température rejoint peu à peu l'ambiant."""
    multiplicateur = Multiplicateur("multiplicateur")
    for _ in range(50):  # phase de chauffe
        multiplicateur.mettre_a_jour(0.0, _contexte(puissance_rotor=2000.0))
    temperature_chaude = multiplicateur.etat["temperature_huile"]
    for _ in range(50):  # plus aucune charge
        multiplicateur.mettre_a_jour(0.0, _contexte(puissance_rotor=0.0))
    assert multiplicateur.etat["temperature_huile"] < temperature_chaude
