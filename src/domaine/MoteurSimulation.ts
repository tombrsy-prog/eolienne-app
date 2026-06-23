import { Systeme } from "./Systeme";
import { Capteur } from "./Capteur";
import { InjecteurAnomalie } from "./Anomalie";

/** Un échantillon = une ligne du jeu de données à un instant t. */
export interface Echantillon {
  t: number;
  mesures: Record<string, number>;
  anormal: number; // 0 = nominal, 1 = anormal (label pour l'IA)
}

/**
 * Moteur de simulation : le coeur générique qui produit les données.
 *
 * À chaque pas de temps, l'enchaînement est toujours le même, quel que soit le système :
 *   1) le système calcule ses grandeurs vraies     (physique)
 *   2) l'injecteur applique les anomalies actives    (vérité perturbée + label)
 *   3) chaque capteur mesure sa grandeur cible        (mesure bruitée)
 *
 * Cette indépendance vis-à-vis du système concret est ce qui satisfait l'exigence
 * de généricité du sujet.
 */
export class MoteurSimulation {
  constructor(
    private systeme: Systeme,
    private capteurs: Capteur[],
    private injecteur: InjecteurAnomalie = new InjecteurAnomalie(),
  ) {}

  simuler(duree: number, pas: number): Echantillon[] {
    const data: Echantillon[] = [];
    for (let t = 0; t <= duree; t = +(t + pas).toFixed(6)) {
      const vraies = this.systeme.grandeurs(t);
      const { grandeurs, anormal } = this.injecteur.transformer(t, vraies);
      const mesures: Record<string, number> = {};
      for (const c of this.capteurs) {
        const valeurVraie = grandeurs[c.cible] ?? NaN;
        mesures[c.nom] = +c.mesurer(valeurVraie).toFixed(4);
      }
      data.push({ t: +t.toFixed(4), mesures, anormal: anormal ? 1 : 0 });
    }
    return data;
  }
}
