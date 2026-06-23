/**
 * Capteur posé sur une grandeur d'un composant.
 *
 * CHOIX DE CONCEPTION — séparer la vérité physique de la mesure :
 * le système produit des grandeurs "vraies" ; le capteur en donne une MESURE
 * entachée de bruit. C'est important car l'IA n'aura accès qu'aux mesures,
 * jamais à la vérité — comme dans la vraie maintenance prédictive.
 */
export class Capteur {
  constructor(
    public readonly nom: string,
    public readonly cible: string, // clé de grandeur, ex. "Palier.temperature"
    public readonly bruit = 0, // écart-type du bruit de mesure
    public readonly unite = "",
  ) {}

  mesurer(valeurVraie: number): number {
    return valeurVraie + this.gaussien() * this.bruit;
  }

  /** Bruit gaussien (Box-Muller) — plus réaliste qu'un bruit uniforme. */
  private gaussien(): number {
    const u = Math.random() || 1e-9;
    const v = Math.random();
    return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
  }
}
