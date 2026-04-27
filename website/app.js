/**
 * app.js — Pynote website
 * Récupère la dernière release stable via l'API GitHub
 * et met à jour les boutons de téléchargement + le badge de version.
 */

const REPO = "marchandbelmontcamille-wq/Pynote";
const API  = `https://api.github.com/repos/${REPO}/releases/latest`;

async function loadLatestRelease() {
  try {
    const res  = await fetch(API, { headers: { "Accept": "application/vnd.github+json" } });
    if (!res.ok) return;
    const data = await res.json();

    const tag  = data.tag_name || "";
    const ver  = tag.replace(/^v/, "");

    // Badge version dans le bouton hero
    const badge = document.getElementById("version-badge");
    if (badge) badge.textContent = ver || "latest";

    // Pointer vers la page de la release (pas téléchargement direct)
    const releaseUrl = data.html_url || `https://github.com/marchandbelmontcamille-wq/Pynote/releases/tag/${data.tag_name}`;

    // Mettre à jour tous les boutons de téléchargement
    ["nav-download", "hero-download", "install-download", "cta-download"].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.href = releaseUrl;
    });

  } catch (e) {
    // En cas d'erreur réseau, les boutons pointent déjà vers /releases/latest
    console.warn("Pynote: impossible de récupérer la version depuis GitHub", e);
  }
}

loadLatestRelease();
