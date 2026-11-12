# LightShift-PatchCore

**Détection d'anomalies industrielles robuste aux changements d'éclairage — prototype local CPU**

## Problématique

PatchCore détecte les défauts en comparant les caractéristiques des images aux patchs normaux d'une banque mémoire. Un changement d'éclairage peut modifier ces caractéristiques sans qu'un défaut soit présent, entraînant :

- **Une dérive de calibration** : l'AUROC reste élevée, mais le seuil d'origine génère davantage de faux positifs (FPR).
- **Une perte de discrimination** : l'AUROC diminue ; modifier uniquement le seuil ne suffit pas.

**Objectif :** étudier ces deux effets et tester quatre améliorations — B1 (banque augmentée), B2 (alignement statistique), B3 (seuil conforme) et B4 (adaptateur appris).

## Environnement et protocole

- **Infrastructure :** Python, PyTorch CPU, Docker, JupyterLab, MLflow.
- **Données :** MVTec AD — `bottle`, `carpet`, `metal_nut` ; résolution 224 × 224.
- **Baseline :** ResNet-18 pré-entraîné et gelé (`layer2` / `layer3`), banque de patchs normaux, coreset et scoring kNN.
- **Précaution :** données sources, validation, adaptation/calibration cible et test séparés ; aucune optimisation de seuil sur le test. Les originaux ne sont pas modifiés.

## Résultats obtenus

### Notebook 01 — Baseline PatchCore

| Catégorie | AUROC image | AP image | AUROC pixel | AU-PRO |
|---|---:|---:|---:|---:|
| Bottle | 97,62 % | 99,13 % | 97,54 % | 94,20 % |
| Carpet | 90,81 % | 97,08 % | 97,86 % | 92,46 % |
| Metal_nut | 82,94 % | 95,24 % | 90,54 % | 84,04 % |

### Notebook 02 — Effet des changements d'éclairage

Cinq perturbations synthétiques ont été évaluées à trois sévérités : luminosité, contraste, gamma, température de couleur et ombrage directionnel.

- **Bottle / luminosité 5 :** AUROC **96,75 %**, mais FPR **100 %** → problème surtout lié au seuil.
- **Carpet / contraste 5 :** AUROC **52,29 %**, FPR **100 %** → dégradation du classement **et** de la calibration.
- **Bottle / ombrage 5 :** AUROC **69,60 %**, FPR **85 %**.
- La dérive des caractéristiques est négativement corrélée à la variation d'AUROC, particulièrement pour `carpet` (`layer3` : Spearman **ρ = −0,978**). Ces corrélations sont exploratoires, non causales.

### Notebook 03 — B2 et B3, version numériquement stabilisée

Les résultats ci-dessous sont des **moyennes descriptives sur 12 conditions** (3 catégories × 4 éclairages, mode rapide), pas des garanties de généralisation.

| Méthode | AUROC image ↑ | F1 ↑ | FPR ↓ |
|---|---:|---:|---:|
| Vanilla | 75,98 % | 82,13 % | 48,07 % |
| **B2 stabilisé** | **81,39 %** | **85,44 %** | 39,02 % |
| B3 seul | 75,98 % | 50,48 % | **5,53 %** |
| B2 + B3 | **81,39 %** | 59,83 % | 6,58 % |

**Interprétation :** B2 améliore l'AUROC moyenne de **5,41 points** et le F1 de **3,31 points** par rapport à Vanilla. B3 abaisse fortement le FPR, mais le seuil conforme peut devenir trop conservateur et faire manquer des défauts : le F1 baisse. La combinaison B2+B3 n'est donc **pas encore la meilleure en F1**.

La stabilisation de B2 a supprimé une explosion numérique observée sur `carpet / contraste 5` : le seuil B2+B3 est passé d'environ **481,01** à **4,318**. Cela corrige la stabilité des scores, sans prouver que la méthode est optimale.

> **Limites actuelles :** évaluation B2/B3 en mode rapide, sans métriques pixel ; calibration sur un petit nombre d'images normales (20 pour B3) ; comparaison CPU utilisant ResNet-18 plutôt que la configuration WideResNet originale. Les performances doivent être validées sur davantage de conditions et avec des expériences répétées.

## Méthodes du projet et suite

| Brique | Rôle | Statut |
|---|---|---|
| **B1** | Banque de patchs normaux augmentés sous différents éclairages, à taille de coreset constante | À implémenter |
| **B2** | Alignement statistique des features | Testé, stabilisé, prometteur |
| **B3** | Calibration conforme d'un seuil sur images normales cibles indépendantes | Testé, compromis FPR/rappel à améliorer |
| **B4** | Adaptateur résiduel 1×1 entraîné sur des vues photométriques, backbone gelé | Prévu sur CPU |

**Prochaines étapes :** notebook 04 (B1), notebook 05 (B4 avec MLflow), puis notebook 06 (ablations B1/B2/B3/B4, robustesse, latence et répétitions). Ne pas régler les hyperparamètres sur le test ; choisir les variantes sur validation.

**Bilan :** les changements d'éclairage dégradent PatchCore par deux mécanismes différents. B2 stabilisé améliore déjà le classement dans plusieurs conditions ; B3 contrôle les faux positifs, mais nécessite d'évaluer explicitement la perte de rappel. Le projet continue avec B1 et B4 avant la comparaison finale.