import { writeFileSync } from "fs";
import { Echantillon } from "../domaine/MoteurSimulation";

/**
 * Écrit un jeu de données au format CSV (lisible par pandas, Excel, TensorFlow...).
 * La colonne "anormal" est l'étiquette qui permettra d'évaluer le modèle d'IA.
 */
export class ExportateurDonnees {
  static versCSV(data: Echantillon[], chemin: string): void {
    if (data.length === 0) return;
    const noms = Object.keys(data[0].mesures);
    const entete = ["t", ...noms, "anormal"].join(",");
    const lignes = data.map((e) =>
      [e.t, ...noms.map((n) => e.mesures[n]), e.anormal].join(","),
    );
    writeFileSync(chemin, [entete, ...lignes].join("\n"), "utf-8");
  }
}
