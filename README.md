# StepFlix

**Watch. Walk. Progress.**

StepFlix est une PWA privée de suivi de tapis de marche/course. Elle transforme les données brutes d'une séance (durée, distance, calories L20, pas, inclinaison, fréquence cardiaque...) en historique et courbes de progression.

## V1

- saisie rapide d'une séance
- vitesse moyenne et allure calculées automatiquement
- conservation séparée des calories affichées par le L20
- estimation calorique personnalisée si un poids est renseigné
- historique des séances
- objectif quotidien de pas
- série de jours actifs
- statistiques semaine / mois / 30 jours / total
- graphiques 7 jours, 8 semaines et vitesse par séance
- PWA installable sur Android
- backend FastAPI + SQLite
- déploiement Docker simple

## Lancer en Docker

```bash
docker compose up -d --build
```

StepFlix écoute uniquement sur :

```
127.0.0.1:8787
```

L'objectif est de le publier ensuite derrière le reverse proxy/Tailscale du serveur, plutôt que d'exposer directement le port sur Internet.

## Données

La base SQLite est créée dans :

```
./data/stepflix.db
```

Le dossier `data/` doit être sauvegardé régulièrement. Les données personnelles ne sont pas stockées dans GitHub.

## Calculs

- **Vitesse moyenne** = distance / durée
- **Allure** = durée / distance
- **Calories L20** = valeur brute saisie depuis l'écran du tapis
- **Calories StepFlix** = estimation distincte à partir de la vitesse moyenne, durée, inclinaison et poids

Les calories StepFlix restent une estimation et ne doivent pas être interprétées comme une mesure physiologique exacte.

## Branche de développement

`feat/stepflix-v1-1`


## GitHub Pages

La version publiée sur GitHub Pages est 100 % statique et fonctionne sans serveur Python.

- les séances sont enregistrées localement dans le navigateur du téléphone
- les paramètres sont enregistrés localement
- aucune donnée personnelle n'est poussée dans GitHub
- Export JSON / Import JSON permet de sauvegarder ou restaurer l'historique
- l'app reste installable comme PWA Android

Le backend FastAPI + SQLite reste dans le dépôt pour une future version synchronisée sur serveur Ubuntu.


## V1.1

- dashboard enrichi : séances semaine, calories estimées et pas StepFlix du mois
- progression avec filtres 8 semaines / 6 mois / 1 an / tout
- courbe des minutes d'activité
- courbe de poids à partir du poids mémorisé lors des séances
- comparaison 30 jours / 30 jours précédents
- bouton d'installation PWA quand le navigateur le permet
- clarification entre calories L20 et estimation StepFlix
- interface mobile affinée jusqu'à 360 px
- audit automatisé Playwright : chargement, création d'une séance, historique, filtres, débordement mobile et captures d'écran


## V1.2 — refonte visuelle

- accueil redessiné pour se rapprocher de la maquette mobile de référence
- cartes compactes avec icônes et métriques colorées
- objectif quotidien circulaire et barre de progression
- série hebdomadaire avec jours actifs
- écran Nouvelle séance plein écran avec grandes cartes de saisie
- panneau de calcul automatique vitesse/allure
- page Progression densifiée avec deux graphiques principaux et deux mini-courbes
- moyennes 7/30 jours et poids actuel
- navigation fixe retravaillée
- mise en page optimisée pour tenir beaucoup plus d'informations dans un écran mobile
- auto-audit Playwright conservé sur les futures branches `feat/stepflix-*`
