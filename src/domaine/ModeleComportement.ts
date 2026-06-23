/**
 * CHOIX DE CONCEPTION — pattern Strategy :
 * la façon dont une grandeur évolue dans le temps est encapsulée dans un objet
 * "modèle de comportement" interchangeable. Un composant compose ses grandeurs
 * à partir de ces modèles, sans coder la physique en dur. On peut ainsi ajouter
 * de nouveaux comportements sans modifier les composants existants (principe ouvert/fermé).
 */
export interface ModeleComportement {
  evaluer(t: number): number;
}

/** Exemple trivial : signal sinusoïdal. À ENRICHIR avec votre physique réelle. */
export class Sinusoide implements ModeleComportement {
  constructor(
    private base: number,
    private amplitude: number,
    private periode: number,
  ) {}
  evaluer(t: number): number {
    return this.base + this.amplitude * Math.sin((2 * Math.PI * t) / this.periode);
  }
}

/** Exemple trivial : rampe lente + bruit (utile pour une dérive thermique). */
export class RampeBruitee implements ModeleComportement {
  constructor(
    private depart: number,
    private pente: number,
    private bruit = 0,
  ) {}
  evaluer(t: number): number {
    return this.depart + this.pente * t + (Math.random() * 2 - 1) * this.bruit;
  }
}

// TODO (à vous) : modèles propres à l'éolienne — puissance fonction du vent,
// régime rotor, température fonction de la charge, etc.
