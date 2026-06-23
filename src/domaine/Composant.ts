/**
 * Grandeurs physiques "vraies" d'un composant à un instant donné.
 * Clé = nom complet de la grandeur (ex. "Palier.temperature"), valeur = mesure physique.
 */
export type Grandeurs = Record<string, number>;

/**
 * Composant abstrait du système technique.
 *
 * CHOIX DE CONCEPTION — pattern Composite :
 * un composant peut contenir d'autres composants (sous-composants). Le système racine
 * est lui-même un composant. C'est ce qui rend le logiciel GÉNÉRIQUE : on assemble
 * n'importe quel système (éolienne, pompe, moteur...) à partir des mêmes briques,
 * sans que le coeur ne connaisse jamais la nature concrète du système.
 *
 * Vos composants d'éolienne (Rotor, Multiplicateur, Génératrice, Roulement...)
 * hériteront simplement de cette classe.
 */
export abstract class Composant {
  protected enfants: Composant[] = [];

  constructor(public readonly nom: string) {}

  ajouter(c: Composant): void {
    this.enfants.push(c);
  }

  get sousComposants(): readonly Composant[] {
    return this.enfants;
  }

  /**
   * Grandeurs physiques propres à CE composant à l'instant t (hors enfants).
   * À implémenter par chaque composant concret : c'est sa "physique".
   */
  abstract grandeursPropres(t: number): Grandeurs;

  /**
   * Grandeurs de ce composant ET de tous ses enfants, préfixées par le nom du composant
   * pour garantir l'unicité des clés dans tout l'arbre. (Parcours récursif du Composite.)
   */
  grandeurs(t: number): Grandeurs {
    const out: Grandeurs = {};
    for (const [k, v] of Object.entries(this.grandeursPropres(t))) {
      out[`${this.nom}.${k}`] = v;
    }
    for (const e of this.enfants) {
      Object.assign(out, e.grandeurs(t));
    }
    return out;
  }
}
