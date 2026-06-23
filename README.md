# Éolienne-app — squelette de démarrage

Générateur **générique** de données pour la maintenance prédictive, avec injection
d'anomalies maîtrisées. Squelette fonctionnel à étendre — la fondation tourne déjà,
à vous de la faire grandir.

## Lancer

```bash
npm install
npm run build
npm start
```

Cela génère `donnees_nominales.csv` et `donnees_anomalie.csv` à partir d'un petit
système de démonstration à deux composants.

## Structure

```
src/
├─ domaine/        Le coeur générique (ne connaît AUCUN système concret)
│  ├─ Composant.ts            classe abstraite + pattern Composite
│  ├─ ComposantParametrable.ts  composant concret piloté par des modèles
│  ├─ ModeleComportement.ts   pattern Strategy (comment une grandeur évolue)
│  ├─ Systeme.ts              racine composite
│  ├─ Capteur.ts              mesure bruitée (vérité physique != mesure)
│  ├─ Anomalie.ts             anomalies maîtrisées + injecteur (labels)
│  └─ MoteurSimulation.ts     boucle temporelle générique
├─ donnees/
│  └─ ExportateurDonnees.ts   export CSV labellisé
└─ demo.ts                    système jouet "hello world" (À REMPLACER)
```

## Choix de conception (à reprendre dans le rapport)

- **Composite** : un système est un composant qui contient des composants -> généricité.
- **Strategy** : les comportements physiques sont des objets interchangeables.
- **Vérité physique vs mesure** : le capteur ajoute du bruit ; l'IA ne voit que la mesure.
- **Anomalie maîtrisée** : début/fin/type connus -> données parfaitement labellisées.
- Le moteur, les capteurs, les anomalies et l'export sont indépendants du système :
  passer du système jouet à l'éolienne ne change QUE `demo.ts`.

## À FAIRE par l'équipe (c'est là votre projet)

- [ ] Modéliser l'éolienne réelle (Rotor, Multiplicateur, Génératrice, Roulement...)
      avec une physique crédible, à la place du système jouet.
- [ ] Ajouter les autres types d'anomalies (Pic, ValeurBloquee, Biais, Degradation).
- [ ] Écrire les **tests unitaires et fonctionnels** (obligatoires).
- [ ] Construire l'IHM web (style app), les courbes, puis la vue 3D Three.js.
- [ ] (Optionnel, partie 2) l'autoencodeur de détection d'anomalies.
- [ ] Internationalisation fr/en, diagrammes UML, Gantt, suivi git.
```
```
