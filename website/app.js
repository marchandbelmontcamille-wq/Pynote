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

    // Trouver l'asset .exe Windows
    const asset = (data.assets || []).find(a => a.name && a.name.endsWith(".exe"));
    const dlUrl = asset ? asset.browser_download_url : data.html_url;

    // Mettre à jour tous les boutons de téléchargement
    ["nav-download", "hero-download", "install-download"].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.href = dlUrl;
    });

  } catch (e) {
    // En cas d'erreur réseau, les boutons pointent déjà vers /releases/latest
    console.warn("Pynote: impossible de récupérer la version depuis GitHub", e);
  }
}

loadLatestRelease();
