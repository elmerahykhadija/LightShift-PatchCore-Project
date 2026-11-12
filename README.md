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

## Notebook 04 — B1 : Banque mémoire augmentée

### Objectif

Améliorer la robustesse de PatchCore aux changements d'éclairage en construisant une banque mémoire à partir d'images normales augmentées (luminosité, contraste, gamma et ombrage), tout en conservant **256 patchs par catégorie**, soit le même budget mémoire que Vanilla.

### Résultats expérimentaux

Les expériences ont été réalisées sur `bottle`, `carpet` et `metal_nut`, en comparant PatchCore Vanilla et B1 sous différentes conditions d'éclairage.

| Métrique | Variation moyenne B1 vs Vanilla |
|---|---:|
| AUROC image | **+8,27 points** |
| F1-score | −10,95 points |
| FPR | −19,51 points |
| Conditions avec amélioration AUROC | 9/12 |

**Résultats marquants :**

- **Bottle :** amélioration de l'AUROC de 69,60 % à 90,40 % sous ombrage sévère (+20,79 points).
- **Carpet :** amélioration sous ombrage (+12,96 points), mais dégradation sous luminosité et contraste élevés.
- **Metal_nut :** gains d'AUROC importants sous luminosité (+23,02 points), contraste (+24,73 points) et ombrage (+21,26 points).

### Interprétation

B1 améliore globalement la capacité de discrimination des anomalies, particulièrement sur `metal_nut` et sous ombrage directionnel. Cependant, le F1 diminue dans plusieurs conditions, ce qui montre qu'une meilleure AUROC ne garantit pas une meilleure décision normal/anormal au seuil utilisé.

**Conclusion :** B1 est prometteur pour améliorer la robustesse du ranking, mais nécessite une meilleure stratégie de calibration pour maintenir un bon compromis entre rappel et faux positifs.

---

## Bilan actuel des méthodes

| Méthode | Gain moyen AUROC | Variation moyenne F1 | État |
|---|---:|---:|---|
| PatchCore Vanilla | Référence | Référence | Baseline validée |
| B1 — Banque augmentée | **+8,27 pts** | −10,95 pts | Prometteur |
| B2 — Alignement statistique | +5,41 pts | **+3,31 pts** | Prometteur |
| B3 — Calibration conforme | 0 pt | −31,65 pts | À améliorer |
| B2+B3 | +5,41 pts | −22,30 pts | Résultats mitigés |
| B4 — Adaptateur appris | — | — | À développer |

*Les résultats sont issus d'expériences préliminaires sur 12 conditions d'éclairage. Ils doivent être confirmés avec davantage de perturbations, de répétitions et une évaluation complète.*

## État d'avancement

- [x] **Notebook 01 :** PatchCore Vanilla, banques mémoire et évaluation.
- [x] **Notebook 02 :** diagnostic des changements d'éclairage et dérive des caractéristiques.
- [x] **Notebook 03 :** B2 + B3, correction de la stabilité numérique et comparaison expérimentale.
- [x] **Notebook 04 :** B1, construction des banques augmentées et comparaison avec Vanilla.
- [ ] **Notebook 05 :** B4, entraînement d'un adaptateur résiduel 1×1 sur CPU avec MLflow.
- [ ] **Notebook 06 :** étude d'ablation des quatre briques, comparaison des combinaisons et évaluation finale.

### Conclusion provisoire

Les expériences confirment que les perturbations d'éclairage peuvent dégrader fortement PatchCore. **B1 et B2 sont actuellement les approches les plus encourageantes pour améliorer l'AUROC**, tandis que B3 permet de réduire les faux positifs, parfois au prix d'une perte importante de rappel.

La prochaine étape consiste à développer B4, puis à comparer les quatre briques individuellement et en combinaison pour identifier la configuration offrant le meilleur compromis entre AUROC, F1, FPR et coût de calcul sur CPU.