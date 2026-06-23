import { Grandeurs } from "./Composant";

/**
 * Anomalie "maîtrisée" : elle transforme une grandeur vraie sur une fenêtre de temps connue.
 *
 * Le caractère MAÎTRISÉ exigé par le sujet vient de là : on connaît exactement quelle
 * grandeur, à partir de quand, jusqu'à quand et de quelle façon elle est perturbée.
 * On peut donc générer des données ANORMALES parfaitement LABELLISÉES, qui serviront
 * à valider le modèle d'IA.
 */
export interface Anomalie {
  readonly cible: string;
  actif(t: number): boolean;
  appliquer(t: number, valeur: number): number;
}

/** Dérive linéaire : la grandeur s'éloigne progressivement de sa valeur nominale. */
export class Derive implements Anomalie {
  constructor(
    public readonly cible: string,
    private debut: number,
    private fin: number,
    private pente: number,
  ) {}
  actif(t: number): boolean {
    return t >= this.debut && t <= this.fin;
  }
  appliquer(t: number, valeur: number): number {
    return valeur + this.pente * (t - this.debut);
  }
}

// TODO (à vous) : implémenter d'autres types, tous avec la même interface Anomalie :
//   - Pic            (valeur aberrante brève)
//   - ValeurBloquee  (capteur figé sur une valeur)
//   - Biais          (décalage constant)
//   - Degradation    (perte d'amplitude / usure)

/**
 * Injecteur : applique toutes les anomalies actives à un instant t et indique
 * si l'échantillon est anormal (c'est l'étiquette / label des données).
 */
export class InjecteurAnomalie {
  private anomalies: Anomalie[] = [];

  ajouter(a: Anomalie): void {
    this.anomalies.push(a);
  }

  transformer(t: number, g: Grandeurs): { grandeurs: Grandeurs; anormal: boolean } {
    const out: Grandeurs = { ...g };
    let anormal = false;
    for (const a of this.anomalies) {
      if (a.actif(t) && a.cible in out) {
        out[a.cible] = a.appliquer(t, out[a.cible]);
        anormal = true;
      }
    }
    return { grandeurs: out, anormal };
  }
}
