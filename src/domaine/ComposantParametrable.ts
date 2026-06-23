import { Composant, Grandeurs } from "./Composant";
import { ModeleComportement } from "./ModeleComportement";

/**
 * Composant générique dont chaque grandeur est pilotée par un modèle de comportement.
 *
 * C'est l'exemple le plus simple de composant concret. Il montre le branchement
 * Composant + Strategy. Vos composants d'éolienne peuvent soit utiliser cette classe
 * telle quelle (en lui passant les bons modèles), soit hériter de Composant pour
 * une physique plus riche (couplage entre grandeurs, état interne, etc.).
 */
export class ComposantParametrable extends Composant {
  constructor(
    nom: string,
    private modeles: Record<string, ModeleComportement>,
  ) {
    super(nom);
  }

  grandeursPropres(t: number): Grandeurs {
    const g: Grandeurs = {};
    for (const [grandeur, modele] of Object.entries(this.modeles)) {
      g[grandeur] = modele.evaluer(t);
    }
    return g;
  }
}
