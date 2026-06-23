import { Systeme } from "./domaine/Systeme";
import { ComposantParametrable } from "./domaine/ComposantParametrable";
import { Sinusoide, RampeBruitee } from "./domaine/ModeleComportement";
import { Capteur } from "./domaine/Capteur";
import { MoteurSimulation, Echantillon } from "./domaine/MoteurSimulation";
import { InjecteurAnomalie, Derive } from "./domaine/Anomalie";

// ============================================================================
//  STARTER WEB (à étendre)
//  ----------------------------------------------------------------------------
//  Cette coquille minimale prouve que le coeur générique tourne DANS LE NAVIGATEUR
//  et affiche les données générées. C'est votre point de départ d'interface.
//  À CONSTRUIRE par-dessus : arborescence du système, courbes temps réel,
//  boutons, internationalisation, et la vue 3D Three.js.
//  (Le système jouet ci-dessous est à remplacer par votre éolienne.)
// ============================================================================

function construireSysteme(): { systeme: Systeme; capteurs: Capteur[] } {
  const systeme = new Systeme("MiniSysteme");
  systeme.ajouter(new ComposantParametrable("Pompe", { pression: new Sinusoide(5, 0.5, 20) }));
  systeme.ajouter(
    new ComposantParametrable("Palier", {
      temperature: new RampeBruitee(40, 0.05, 0.3),
      vibration: new Sinusoide(2, 0.2, 5),
    }),
  );
  const capteurs = [
    new Capteur("c_pression", "Pompe.pression", 0.05, "bar"),
    new Capteur("c_temp", "Palier.temperature", 0.2, "°C"),
    new Capteur("c_vib", "Palier.vibration", 0.05, "mm/s"),
  ];
  return { systeme, capteurs };
}

function simuler(avecAnomalie: boolean): Echantillon[] {
  const { systeme, capteurs } = construireSysteme();
  const injecteur = new InjecteurAnomalie();
  if (avecAnomalie) injecteur.ajouter(new Derive("Palier.temperature", 60, 120, 0.4));
  return new MoteurSimulation(systeme, capteurs, injecteur).simuler(120, 1);
}

function telechargerCSV(data: Echantillon[], nom: string): void {
  const noms = Object.keys(data[0].mesures);
  const entete = ["t", ...noms, "anormal"].join(",");
  const lignes = data.map((e) => [e.t, ...noms.map((n) => e.mesures[n]), e.anormal].join(","));
  const blob = new Blob([[entete, ...lignes].join("\n")], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = nom;
  a.click();
  URL.revokeObjectURL(url);
}

function rendre(avecAnomalie: boolean): void {
  const data = simuler(avecAnomalie);
  const noms = Object.keys(data[0].mesures);
  const app = document.getElementById("app")!;
  const lignes = data
    .slice(0, 12)
    .map(
      (e) =>
        `<tr><td>${e.t}</td>${noms.map((n) => `<td>${e.mesures[n]}</td>`).join("")}<td>${e.anormal}</td></tr>`,
    )
    .join("");

  app.innerHTML = `
    <main style="font-family:system-ui,sans-serif;max-width:760px;margin:24px auto;padding:0 16px">
      <h1 style="font-size:20px">GADMAPS — démo web</h1>
      <p style="color:#555">Le coeur générique tourne dans le navigateur et génère un jeu de données.
      ${avecAnomalie ? "<b>Une anomalie (dérive de température) est injectée à partir de t=60.</b>" : "Données nominales."}</p>
      <div style="margin:12px 0;display:flex;gap:8px;flex-wrap:wrap">
        <button id="btn-nom">Données nominales</button>
        <button id="btn-ano">Injecter une anomalie</button>
        <button id="btn-csv">Télécharger le CSV</button>
      </div>
      <p style="color:#777;font-size:13px">12 premières lignes sur ${data.length} :</p>
      <table border="1" cellpadding="6" style="border-collapse:collapse;font-size:13px">
        <thead><tr><th>t</th>${noms.map((n) => `<th>${n}</th>`).join("")}<th>anormal</th></tr></thead>
        <tbody>${lignes}</tbody>
      </table>
    </main>`;

  document.getElementById("btn-nom")!.addEventListener("click", () => rendre(false));
  document.getElementById("btn-ano")!.addEventListener("click", () => rendre(true));
  document
    .getElementById("btn-csv")!
    .addEventListener("click", () => telechargerCSV(data, avecAnomalie ? "anomalie.csv" : "nominal.csv"));
}

rendre(false);
