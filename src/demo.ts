import { Systeme } from "./domaine/Systeme";
import { ComposantParametrable } from "./domaine/ComposantParametrable";
import { Sinusoide, RampeBruitee } from "./domaine/ModeleComportement";
import { Capteur } from "./domaine/Capteur";
import { MoteurSimulation } from "./domaine/MoteurSimulation";
import { InjecteurAnomalie, Derive } from "./domaine/Anomalie";
import { ExportateurDonnees } from "./donnees/ExportateurDonnees";

// ============================================================================
//  SYSTÈME JOUET (hello world)
//  ----------------------------------------------------------------------------
//  Ce mini-système à 2 composants ne sert qu'à PROUVER que l'architecture tourne
//  de bout en bout. À REMPLACER par votre éolienne :
//    Systeme("Eolienne") -> Rotor, Multiplicateur, Génératrice, Roulement principal
//  Le reste du code (moteur, capteurs, anomalies, export) ne changera PAS :
//  c'est tout l'intérêt d'un coeur générique.
// ============================================================================

const systeme = new Systeme("MiniSysteme");

systeme.ajouter(
  new ComposantParametrable("Pompe", {
    pression: new Sinusoide(5, 0.5, 20), // bar
  }),
);
systeme.ajouter(
  new ComposantParametrable("Palier", {
    temperature: new RampeBruitee(40, 0.05, 0.3), // °C
    vibration: new Sinusoide(2, 0.2, 5), // mm/s
  }),
);

const capteurs = [
  new Capteur("c_pression", "Pompe.pression", 0.05, "bar"),
  new Capteur("c_temp", "Palier.temperature", 0.2, "°C"),
  new Capteur("c_vib", "Palier.vibration", 0.05, "mm/s"),
];

// 1) Données NOMINALES (pour entraîner l'IA)
const nominal = new MoteurSimulation(systeme, capteurs).simuler(120, 1);
ExportateurDonnees.versCSV(nominal, "donnees_nominales.csv");

// 2) Données avec ANOMALIE maîtrisée : dérive thermique du palier de t=60 à t=120
const injecteur = new InjecteurAnomalie();
injecteur.ajouter(new Derive("Palier.temperature", 60, 120, 0.4));
const anormal = new MoteurSimulation(systeme, capteurs, injecteur).simuler(120, 1);
ExportateurDonnees.versCSV(anormal, "donnees_anomalie.csv");

console.log(`Nominal  : ${nominal.length} échantillons -> donnees_nominales.csv`);
console.log(
  `Anomalie : ${anormal.length} échantillons (${anormal.filter((e) => e.anormal).length} anormaux) -> donnees_anomalie.csv`,
);
console.log("Aperçu nominal  (t=0)  :", nominal[0]);
console.log("Aperçu anomalie (t=70) :", anormal.find((e) => e.t === 70));
