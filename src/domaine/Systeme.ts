import { Composant, Grandeurs } from "./Composant";

/**
 * Le système racine. C'est un Composant composite qui n'a pas de grandeurs propres :
 * il ne fait qu'agréger ses composants. On l'instancie puis on lui ajoute des composants.
 */
export class Systeme extends Composant {
  grandeursPropres(_t: number): Grandeurs {
    return {};
  }
}
