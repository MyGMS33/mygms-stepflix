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

`feat/stepflix-v1`
