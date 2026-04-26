# Mentions légales & RGPD — Pynote

## 1. Nature du projet

Pynote est un **logiciel libre open source** (licence MIT) permettant aux
élèves d'afficher leur emploi du temps et leurs devoirs depuis la plateforme
Pronote d'Index Éducation.

Ce projet est **indépendant** et n'est pas affilié, approuvé ni sponsorisé par
Index Éducation.

---

## 2. Données personnelles traitées (RGPD)

### Données collectées

Pynote traite les données suivantes **uniquement en local sur votre appareil** :

| Donnée | Finalité | Durée de conservation |
|---|---|---|
| URL Pronote | Connexion au serveur de l'établissement | Jusqu'à déconnexion |
| Identifiant Pronote | Authentification | Jusqu'à déconnexion |
| Mot de passe Pronote | Authentification initiale | Non sauvegardé en clair* |
| `client_identifier` (token) | Reconnexion automatique | Jusqu'à déconnexion |
| UUID appareil | Identification du dispositif | Jusqu'à déconnexion |
| Emploi du temps, devoirs | Affichage | En mémoire uniquement, non persisté |

> *Le mot de passe est utilisé une seule fois pour la connexion initiale. Les
> connexions suivantes utilisent le `client_identifier` (token Pronote).

### Stockage

Le fichier `%APPDATA%/Pynote/session.json` contient les credentials de session.
Il est stocké **localement sur votre appareil uniquement**.

**Pynote ne transmet aucune donnée à un serveur tiers.** Toutes les requêtes
sont effectuées directement vers le serveur Pronote de votre établissement.

### Droits des utilisateurs (RGPD)

Vous pouvez à tout moment :
- **Supprimer vos données** : cliquez sur "Déconnexion" dans l'app, ou
  supprimez manuellement `%APPDATA%/Pynote/session.json`
- **Accéder à vos données** : ouvrez le fichier `session.json`

---

## 3. Responsabilité

Pynote utilise la bibliothèque **pronotepy** (https://github.com/bain3/pronotepy)
pour communiquer avec les serveurs Pronote. L'utilisation de cette API non
officielle est soumise aux conditions d'utilisation d'Index Éducation.

L'auteur de Pynote décline toute responsabilité en cas :
- De blocage de compte Pronote
- De modification de l'API Pronote rendant l'application non fonctionnelle
- De perte de données

---

## 4. Dépendances open source

| Bibliothèque | Licence | Lien |
|---|---|---|
| `pronotepy` | MIT | https://github.com/bain3/pronotepy |
| `customtkinter` | MIT | https://github.com/TomSchimansky/CustomTkinter |
| `python-dotenv` | BSD | https://github.com/theskumar/python-dotenv |

---

## 5. Contact

Pour toute question relative à la vie privée ou aux données personnelles :
👉 https://github.com/marchandbelmontcamille-wq/Pynote/issues

---

## 6. Propriété intellectuelle & assistance IA

Ce projet a été développé avec l'assistance d'un outil d'intelligence artificielle
(Roo/Claude d'Anthropic). Conformément au droit français et aux conditions
d'utilisation d'Anthropic :

- **L'IA ne peut pas être titulaire de droits d'auteur** (elle n'a pas de
  personnalité juridique — articles L111-1 et L113-1 du Code de la propriété
  intellectuelle)
- **Le code, l'architecture et les décisions de conception appartiennent à
  l'auteur du projet** (`marchandbelmontcamille-wq`), qui a fourni les
  spécifications, dirigé le développement et validé chaque composant
- Les CGU d'Anthropic (https://www.anthropic.com/legal/usage-policy) stipulent
  que les outputs générés appartiennent à l'utilisateur

Ce projet est donc bien protégé par la licence MIT au nom de son auteur.

---

*Dernière mise à jour : Avril 2026*
