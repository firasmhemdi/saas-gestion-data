# SaaS Gestion Data — Backlog Produit & Planification des Sprints

Projet : Plateforme SaaS de collecte, centralisation et exploitation des données
environnementales pour l'industrie.
Référence : cahier des charges « SaaS Gestion Data ».

---

## 1. Vision & périmètre

La solution couvre 5 couches fonctionnelles :

| Couche | Contenu |
|---|---|
| Collecte & Automatisation | Connecteurs ERP, fichiers, SQL, API, IoT, extraction documentaire |
| Data Processing | Nettoyage, mapping, normalisation, contrôle qualité |
| Base de données environnementale | Référentiel central structuré, multi-tenant |
| Analytics & IA | Indicateurs, moteur RAG, agrégations |
| Restitution | Dashboards, rapports, assistant conversationnel |

Sécurité transverse : JWT, RBAC, multi-tenant, chiffrement, audit.

---

## 2. Backlog Produit (Product Backlog)

Légende priorité (MoSCoW) : **M**ust / **S**hould / **C**ould / **W**on't (cette itération).
Estimation en points (Fibonacci). Sprint cible : numéro du sprint où le PBI est planifié.

### Release 1 — Fondations & Sécurité

| ID | PBI | Priorité | Pts | Sprint |
|---|---|---|---|---|
| PB-01 | Authentification JWT (register, login, refresh, logout, me) | M | 5 | 1 ✅ |
| PB-02 | Gestion des rôles RBAC (admin, resp. env., consultant, lecture seule) | M | 5 | 1 ✅ |
| PB-03 | Isolation multi-tenant par entreprise cliente | M | 5 | 1 ✅ |
| PB-04 | Journal d'audit des actions sensibles (connexions, exports, modifs) | M | 3 | 1 ✅ |
| PB-05 | Frontend d'authentification (login, register, dashboard, gestion utilisateurs, audit) | M | 8 | 1 ✅ |
| PB-06 | Modèle de données environnemental (Sites, DataSources, Indicateurs, Émissions…) | M | 8 | 2 ✅ |
| PB-07 | CRUD des Sites industriels (par tenant) | M | 5 | 2 ✅ |
| PB-08 | CRUD des Sources de données (DataSources) | M | 5 | 2 ✅ |
| PB-09 | Migrations de schéma (Alembic) + seed de démonstration | S | 3 | 2 ✅ |
| PB-10 | Chiffrement au repos (AES-256) et en transit (TLS 1.2+) | S | 5 | 2 ✅ |
| PB-41 | Double authentification (OTP) — code à 6 chiffres, anti-rejeu, activation | M | 3 | 2 ✅ |

### Release 2 — Collecte & Intégration

| ID | PBI | Priorité | Pts | Sprint |
|---|---|---|---|---|
| PB-11 | Import de fichiers Excel/CSV (upload, aperçu, mapping de colonnes) | M | 8 | 3 |
| PB-12 | Connecteur API externe (config OAuth2/clé API, test de connexion) | M | 8 | 3 |
| PB-13 | Connecteur SQL en lecture seule (config, test) | M | 8 | 3 |
| PB-14 | Traçabilité des imports (logs, horodatage, statut, volumétrie) | M | 5 | 3 |
| PB-15 | Connecteur ERP MVP (Odoo) — extraction via API native | M | 13 | 4 |
| PB-16 | Data Mapping automatique source → modèle interne | M | 8 | 4 |
| PB-17 | Planification de la synchronisation (fréquence, fenêtre horaire) | S | 5 | 4 |
| PB-18 | Gestion des erreurs connecteur (retry, alertes, journal) | M | 5 | 4 |
| PB-19 | Agent on-premise d'intégration (déploiement chez le client) | C | 8 | — |
| PB-20 | Collecte de données IoT (compteurs, débitmètres) | C | 8 | — |

### Release 3 — Traitement documentaire & Qualité

| ID | PBI | Priorité | Pts | Sprint |
|---|---|---|---|---|
| PB-21 | Upload de documents (factures, bordereaux, contrats) | M | 5 | 5 |
| PB-22 | Pipeline OCR (Tesseract / PaddleOCR) sur PDF/scans | M | 8 | 5 |
| PB-23 | Classification automatique du type de document | M | 5 | 5 |
| PB-24 | Extraction NLP des champs (montants, quantités, dates, unités, fournisseurs) | M | 8 | 5 |
| PB-25 | Validation humaine + interface de correction | M | 5 | 5 |
| PB-26 | Normalisation des unités (kWh, m³, tonnes, litres…) | M | 5 | 6 |
| PB-27 | Contrôle qualité (valeurs manquantes/aberrantes, doublons) + alertes | M | 8 | 6 |
| PB-28 | Workflow de validation avant intégration au référentiel | S | 5 | 6 |
| PB-29 | Apprentissage progressif du mapping (corrections utilisateur) | S | 8 | 6 |

### Release 4 — Analytics & Restitution

| ID | PBI | Priorité | Pts | Sprint |
|---|---|---|---|---|
| PB-30 | Calcul des indicateurs environnementaux (énergie, eau, déchets) | M | 8 | 7 |
| PB-31 | Calcul des émissions carbone par scope (1, 2, 3) | M | 8 | 7 |
| PB-32 | Dashboard ESG (agrégations, comparaisons multi-sites) | M | 8 | 7 |
| PB-33 | Rapports exportables (ESG, BEGES, personnalisés) | S | 5 | 7 |
| PB-34 | Indexation vectorielle des documents et données (pgvector) | M | 8 | 8 |
| PB-35 | Assistant conversationnel RAG (langage naturel, filtre SQL + recherche vectorielle) | M | 13 | 8 |
| PB-36 | Citation systématique des sources dans les réponses IA | M | 5 | 8 |
| PB-37 | Historique des requêtes IA (table AIQueries) | S | 3 | 8 |

### Transverse

| ID | PBI | Priorité | Pts | Sprint |
|---|---|---|---|---|
| PB-38 | Déploiement Docker (compose déjà en place) + orchestration | M | 5 | en continu |
| PB-39 | Documentation API (Swagger) + docs installation/exploitation | M | 3 | en continu |
| PB-40 | CI/CD (tests automatiques, build image) | C | 5 | — |

---

## 3. Planification des Releases / Sprints

| Release | Sprint | Période | Objectif / Livrable incrémental |
|---|---|---|---|
| **R1 — Fondations** | Sprint 1 | Semaines 1-2 | ✅ Authentification JWT + RBAC + multi-tenant + audit + frontend auth. **Valeur : plateforme accessible et sécurisée.** |
| | Sprint 2 | Semaines 3-4 | ✅ Référentiel multi-tenant (Sites, Sources, indicateurs, émissions, saisie manuelle) + chiffrement AES-256 + double authentification OTP. **Valeur : stocker et sécuriser les données structurées.** |
| **R2 — Collecte & Intégration** | Sprint 3 | Semaines 5-6 | Import fichiers Excel/CSV + connecteurs API et SQL + traçabilité. **Valeur : alimenter le référentiel.** |
| | Sprint 4 | Semaines 7-8 | Connecteur ERP MVP (Odoo), mapping automatique, planification, erreurs. **Valeur : automatiser la collecte ERP.** |
| **R3 — Documentaire & Qualité** | Sprint 5 | Semaines 9-10 | Pipeline OCR/NLP + validation humaine des documents. **Valeur : extraire les factures.** |
| | Sprint 6 | Semaines 11-12 | Normalisation, contrôle qualité, workflow de validation, apprentissage. **Valeur : données fiables.** |
| **R4 — Analytics & Restitution** | Sprint 7 | Semaines 13-14 | Indicateurs, émissions, dashboard ESG, rapports. **Valeur : piloter la performance environnementale.** |
| | Sprint 8 | Semaines 15-16 | Assistant IA RAG + citations + historique. **Valeur : interroger en langage naturel.** |

Hypothèse : 1 sprint = 2 semaines ; vélocité cible ≈ 20-26 points/sprint ; équipe 1-2 développeurs.

---

## 4. Backlog de chaque Sprint

### Sprint 1 — Authentification, RBAC, multi-tenant, audit ✅ (terminé)

**Objectif :** mettre en place l'authentification sécurisée de la plateforme (JWT), le modèle de rôles,
l'isolation multi-tenant et la journalisation d'audit, côté backend et frontend.

**User stories :**
- US-01.1 En tant que nouvel utilisateur, je peux m'inscrire avec mon entreprise afin de créer mon tenant et devenir admin.
  - Critères : `/register` crée la Company + l'User admin ; un email déjà utilisé → 409 ; mot de passe < 8 car. → 422.
- US-01.2 En tant qu'utilisateur, je peux me connecter afin d'obtenir un token d'accès.
  - Critères : login réussi → `access_token` + `refresh_token` ; identifiants invalides → 401 ; échec journalisé.
- US-01.3 En tant qu'utilisateur, je peux rafraîchir ma session.
  - Critères : rotation du refresh token ; ancien token réutilisé → 401 ; token révoqué/expiré → 401.
- US-01.4 En tant qu'utilisateur, je peux me déconnecter.
  - Critères : refresh token révoqué en base ; toute tentative de réutilisation → 401.
- US-01.5 En tant que membre, je peux consulter mon profil (`/me`).
- US-01.6 En tant qu'admin, je peux créer des utilisateurs de mon entreprise avec un rôle.
- US-01.7 En tant qu'admin, je peux modifier le rôle d'un utilisateur (mais pas le mien).
- US-01.8 En tant que non-admin, je ne peux pas accéder à l'administration des utilisateurs (403).
- US-01.9 En tant qu'admin, je peux consulter le journal d'audit de mon entreprise.

**Tâches techniques :**
- Backend : modèle User/Company/RefreshToken/AuditLog, hash bcrypt, émission JWT, endpoints auth, RBAC, endpoints utilisateurs, journal d'audit.
- Frontend : client API (auto-refresh), AuthProvider, pages login/register/dashboard/users/audit, middleware de protection des routes.
- Tests : 21 tests pytest ✅ ; build Next.js ✅ ; lint ✅.

### Sprint 2 — Modèle de données & Référentiel multi-tenant ✅ (terminé)

**Objectif :** construire le référentiel environnemental structuré, isolé par tenant, sécurisé.

**User stories :**
- US-02.1 En tant qu'admin, je peux créer des sites industriels rattachés à mon entreprise.
- US-02.2 En tant qu'utilisateur, je ne vois que les sites de mon entreprise (isolation tenant).
- US-02.3 En tant qu'admin, je peux configurer des sources de données (ERP, fichier, API, capteur).
- US-02.4 En tant que responsable, je peux consulter le référentiel des indicateurs environnementaux (énergie, eau, déchets, émissions).
- US-02.5 En tant qu'utilisateur, je peux saisir manuellement des données manquantes (formulaire).
- US-02.6 En tant qu'utilisateur, je peux activer la double authentification (OTP) et me connecter avec un code à 6 chiffres.

**Tâches techniques :** tables Sites, DataSources, EnvironmentalIndicators, Emissions, EnvironmentalData ; migrations Alembic ; chiffrement AES-256 des champs sensibles (config de DataSource) ; CRUD frontend (sites, sources, référentiel, saisie manuelle avec workflow de validation) ; OTP backend (challenge + vérification anti-rejeu) et frontend (connexion 2 étapes) ; tests pytest ✅ (51 tests cumulés) ; build Next.js ✅ ; lint ✅.

### Sprint 3 — Collecte : fichiers, API, SQL, traçabilité

**Objectif :** permettre l'ingestion de données depuis fichiers plats, API externes et bases SQL en lecture seule, avec traçabilité complète.

**User stories :**
- US-03.1 En tant que responsable, je peux importer un fichier Excel/CSV (aperçu + mapping des colonnes).
- US-03.2 En tant que responsable, je peux configurer une source API (OAuth2/clé API) et tester la connexion.
- US-03.3 En tant que responsable, je peux configurer une base SQL en lecture seule et tester la connexion.
- US-03.4 En tant qu'admin, je consulte l'historique des imports (statut, volumétrie, durée).
- US-03.5 En tant que système, j'assure une reprise sur erreur (file d'attente).

**Tâches techniques :** gestion des uploads (fastapi-uploads), parsing pandas/openpyxl, gestionnaire de connecteurs (API REST, SQLAlchemy/ODBC lecture seule), files de messages (RabbitMQ) pour la synchronisation asynchrone, logs d'import.

### Sprint 4 — Connecteur ERP MVP + Mapping

**Objectif :** connecter un ERP type (Odoo) en extraction automatique et appliquer le mapping vers le modèle interne.

**User stories :**
- US-04.1 En tant que responsable, je peux configurer une connexion ERP (OAuth2/clé API) sans écriture dans le système source.
- US-04.2 En tant que système, j'extrais les données via l'API native de l'ERP.
- US-04.3 En tant que responsable, je définis la correspondance champs source → champs modèle (product_qty → quantity, etc.).
- US-04.4 En tant que responsable, je planifie la synchronisation (fréquence, périmètre, fenêtre horaire).
- US-04.5 En tant que système, je détecte les échecs, je retente et j'alerte.

**Tâches techniques :** connecteur Odoo (XML-RPC/JSON-RPC), moteur de mapping configurable, planification (APScheduler/Celery), gestion des erreurs + alertes, UI de configuration des connexions.

### Sprint 5 — Extraction documentaire (OCR/NLP)

**Objectif :** automatiser l'extraction de données structurées depuis factures et bordereaux.

**User stories :**
- US-05.1 En tant que responsable, je peux déposer un document (PDF/scanné).
- US-05.2 En tant que système, je classe automatiquement le type de document (facture énergie, bordereau…).
- US-05.3 En tant que système, j'extrais les champs pertinents (montants, quantités, dates, unités, fournisseurs) via OCR + NLP.
- US-05.4 En tant qu'utilisateur, je peux valider ou corriger l'extraction avant intégration.

**Tâches techniques :** pipeline OCR (Tesseract/PaddleOCR), classification (modèle), extraction de champs (regex + NLP), interface de correction, stockage des Documents/ExtractedData.

### Sprint 6 — Qualité, Normalisation & Mapping progressif

**Objectif :** garantir la fiabilité des données intégrées.

**User stories :**
- US-06.1 En tant que système, je normalise les unités (kWh, m³, tonnes, litres).
- US-06.2 En tant que système, je détecte les valeurs manquantes/aberrantes et les doublons.
- US-06.3 En tant que responsable, je reçois des alertes qualité (valeur hors plage, incohérence temporelle).
- US-06.4 En tant que responsable, je valide les données avant intégration au référentiel.
- US-06.5 En tant que système, j'améliore le mapping à partir des corrections utilisateur.

**Tâches techniques :** moteur de règles qualité, normalisation d'unités, workflow de validation, mécanisme d'apprentissage du mapping.

### Sprint 7 — Indicateurs, Émissions & Dashboard ESG

**Objectif :** calculer les indicateurs et restituer la performance environnementale.

**User stories :**
- US-07.1 En tant que responsable, je consulte la consommation d'énergie/ eau et la production de déchets par site.
- US-07.2 En tant que responsable, je consulte les émissions carbone par scope (1, 2, 3).
- US-07.3 En tant que responsable, je compare les performances entre sites.
- US-07.4 En tant qu'utilisateur, j'exporte des rapports (ESG, BEGES, personnalisé).

**Tâches techniques :** calculs des indicateurs (services), agrégations temporelles, graphiques (Recharts/Chart.js), génération de rapports (PDF/Excel).

### Sprint 8 — Assistant IA RAG & Restitution finale

**Objectif :** permettre l'interrogation des données en langage naturel avec des réponses sourcées.

**User stories :**
- US-08.1 En tant qu'utilisateur, je pose une question en langage naturel sur les données environnementales.
- US-08.2 En tant que système, je combine recherche sémantique (vectorielle) et filtrage structuré (SQL).
- US-08.3 En tant que système, je cite les sources utilisées (document, indicateur, période).
- US-08.4 En tant que responsable, je consulte l'historique de mes requêtes IA.
- US-08.5 Exemple : « Quel site possède la consommation électrique la plus élevée ? » → site + valeur + période + sources.

**Tâches techniques :** indexation vectorielle (pgvector), pipeline RAG (LangChain + LLM), base vectorielle dédiée par tenant, interface conversationnelle, table AIQueries.

---

## 5. Définition de Done (transverse)

Un PBI est « done » quand :
1. Code implémenté et revu ; pas de régression.
2. Tests automatisés (pytest backend, tests frontend si applicable) passent.
3. Build et lint propres (`npm run build`, `npm run lint`, `pytest`).
4. Documentation API mise à jour (Swagger).
5. Démo utilisable en local (docker compose + frontend).
6. Migration de schéma versionnée (si modèle impacté).

---

## 6. État d'avancement

| Release | Sprint | Statut |
|---|---|---|
| R1 | Sprint 1 | ✅ Terminé (21 tests, build + lint OK) |
| R1 | Sprint 2 | ✅ Terminé (51 tests cumulés, build + lint OK) |
| R2 | Sprint 3 | ⏳ Planifié |
| R2 | Sprint 4 | ⏳ Planifié |
| R3 | Sprint 5 | ⏳ Planifié |
| R3 | Sprint 6 | ⏳ Planifié |
| R4 | Sprint 7 | ⏳ Planifié |
| R4 | Sprint 8 | ⏳ Planifié |
