# Politique de sécurité — Pynote

## Versions supportées

| Version | Support sécurité |
|---|---|
| `dev` (branche) | ✅ Actif |
| Releases publiées | ✅ Actif |

## Signaler une vulnérabilité

Si vous découvrez une faille de sécurité dans Pynote, **ne créez pas d'issue publique**.

Contactez directement le mainteneur via les **GitHub Security Advisories** :
👉 https://github.com/marchandbelmontcamille-wq/Pynote/security/advisories/new

Incluez dans votre rapport :
- Description de la vulnérabilité
- Étapes pour la reproduire
- Impact potentiel
- Version / commit concerné

Vous recevrez une réponse dans les 72 heures.

## Données sensibles

Pynote stocke les credentials Pronote **localement uniquement** dans
`%APPDATA%/Pynote/session.json`. Ce fichier n'est jamais transmis à un serveur
tiers. Il est exclu du dépôt Git via `.gitignore`.

Ne partagez jamais ce fichier ni son contenu.
