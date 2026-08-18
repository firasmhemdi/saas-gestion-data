# SaaS Gestion Data — Backlog Produit & Planification des Sprints

Projet : Plateforme SaaS de collecte, centralisation et exploitation des données environnementales pour l'industrie.

## Introduction générale

Le présent document formalise la gestion de projet agile du projet **SaaS Gestion Data** : plateforme SaaS de collecte, centralisation et exploitation des données environnementales (énergie, eau, déchets, émissions, matières) pour l'industrie. Il définit le **Product Backlog** (liste priorisée des fonctionnalités du produit), la **planification des Releases et des Sprints** ainsi que le **backlog détaillé de chaque sprint**. Ce document s'appuie sur le cahier des charges du projet et suit la méthodologie **SCRUM**.

---

## Chapitre 1 : Cadre général du projet

### 1.1 Présentation du projet

Le projet **SaaS Gestion Data** est une plateforme web de type SaaS qui permet de :

- centraliser l'ensemble des données environnementales (énergie, eau, déchets, émissions, matières) dans un référentiel unique ;
- automatiser la collecte depuis les systèmes existants du client (ERP, bases SQL, fichiers, capteurs IoT, saisie manuelle) ;
- transformer les données brutes hétérogènes en données structurées et exploitables (mapping, normalisation d'unités) ;
- fournir une interface intelligente basée sur l'IA permettant l'interrogation des données en langage naturel (assistant RAG).

### 1.2 Objectifs fonctionnels du projet

- Centraliser les données environnementales dans un référentiel multi-tenant.
- Automatiser la collecte et la synchronisation des données (ERP, SQL, fichiers, API, IoT).
- Garantir la qualité des données (nettoyage, dédoublonnage, contrôle qualité).
- Calculer les indicateurs environnementaux et les émissions carbone.
- Restituer les résultats (dashboard ESG, rapports) et interroger les données via un assistant IA.

### 1.3 Architecture fonctionnelle de la solution

| Couche | Rôle |
|---|---|
| Sources de données | Systèmes existants chez le client, hétérogènes par nature |
| Collecte & Automatisation | Connecteurs, agents, synchronisation, extraction documentaire |
| Data Processing | Nettoyage, mapping, normalisation, validation qualité |
| Base de données environnementale | Référentiel central structuré, multi-tenant |
| Analytics & IA | Calculs d'indicateurs, moteur RAG, agrégations |
| Restitution | Dashboards, rapports exportables, assistant conversationnel |

### 1.4 Méthodologie de travail

La méthodologie retenue est **SCRUM**, méthode agile itérative et incrémentale. Le projet est découpé en **4 Releases**, chacune regroupant une série de **Sprints** de 3 semaines. Chaque sprint produit un **incrément potentiellement livrable** (définition de « done » : code testé, documentation API mise à jour, build et lint propres, démo utilisable).

| Rôle | Nom |
|---|---|
| Équipe de développement | Firas Mhemdi — Moatez Hmida |
| Product Owner (encadrant académique) | Houneida Haddaji |
| Scrum Master (encadrant professionnel) | Dalel Loussaief |

---

## Chapitre 2 : Backlog du produit

### 2.1 Définition du Product Backlog

Le **Product Backlog** est une liste d'éléments (fonctionnalités) nécessaires pour atteindre les objectifs du produit, classée par ordre de priorité. Il permet aux membres de l'équipe de suivre leurs tâches. Dans cette partie, nous divisons les fonctionnalités en **7 modules (épiques)**. Pour chaque module, nous présentons les différentes **user stories** en indiquant leur **priorité** (Élevée / Moyenne / Faible) et leur **point d'effort** (Fibonacci).

### 2.2 Backlog du produit

Le tableau 2.1 présente le backlog complet du produit.

| Épique | Fonctionnalité | ID | User Stories | Point d'effort | Priorité |
|---|---|---|---|---|---|
| Module Authentification & Sécurité | Authentification sécurisée (JWT) | 1 | En tant qu'utilisateur, je veux m'authentifier de manière sécurisée afin d'accéder à mon espace. | 5 | Élevée |
| Module Authentification & Sécurité | Gestion des profils utilisateurs | 2 | En tant qu'utilisateur, je veux gérer mon profil afin de fournir des informations actualisées. | 5 | Élevée |
| Module Authentification & Sécurité | Gestion des rôles (RBAC) | 3 | En tant qu'admin, je veux gérer les rôles des utilisateurs afin de contrôler les accès. | 5 | Élevée |
| Module Authentification & Sécurité | Isolation multi-tenant | 4 | En tant que client, je veux que mes données soient strictement isolées afin de garantir la confidentialité. | 5 | Élevée |
| Module Authentification & Sécurité | Journal d'audit | 5 | En tant qu'admin, je veux consulter le journal d'audit afin de tracer les actions sensibles. | 3 | Élevée |
| Module Authentification & Sécurité | Chiffrement des données | 6 | En tant qu'admin, je veux que les données sensibles soient chiffrées afin de garantir leur sécurité. | 5 | Moyenne |
| Module Authentification & Sécurité | Double authentification (OTP) | 7 | En tant qu'utilisateur, je veux renforcer ma connexion avec un code à 6 chiffres afin de sécuriser l'accès. | 3 | Élevée |
| Module Collecte & Automatisation | Import de fichiers Excel/CSV | 8 | En tant que responsable environnement, je veux importer des fichiers Excel/CSV afin d'alimenter le référentiel. | 8 | Élevée |
| Module Collecte & Automatisation | Connecteur API externe | 9 | En tant que responsable environnement, je veux configurer une source API afin d'automatiser la collecte. | 8 | Élevée |
| Module Collecte & Automatisation | Connecteur SQL en lecture seule | 10 | En tant que responsable environnement, je veux connecter une base SQL en lecture seule afin de collecter sans modifier le système source. | 8 | Élevée |
| Module Collecte & Automatisation | Connecteur ERP (Odoo) | 11 | En tant que responsable environnement, je veux connecter un ERP afin d'extraire automatiquement les données. | 13 | Élevée |
| Module Collecte & Automatisation | Synchronisation planifiée | 12 | En tant que responsable environnement, je veux planifier la synchronisation afin d'automatiser la collecte. | 5 | Moyenne |
| Module Collecte & Automatisation | Traçabilité des imports | 13 | En tant qu'admin, je veux consulter les logs d'import afin de tracer les échanges et leur statut. | 5 | Élevée |
| Module Collecte & Automatisation | Collecte de données IoT | 14 | En tant que responsable environnement, je veux collecter les données des capteurs IoT afin de mesurer en temps réel. | 8 | Faible |
| Module Collecte & Automatisation | Agent d'intégration on-premise | 15 | En tant qu'admin, je veux déployer un agent d'intégration chez le client afin de collecter sans accès direct au SI. | 8 | Faible |
| Module Extraction documentaire | Dépôt de documents | 16 | En tant que responsable environnement, je veux déposer des documents (factures, bordereaux, contrats) afin de les traiter. | 5 | Élevée |
| Module Extraction documentaire | Pipeline OCR | 17 | En tant que responsable environnement, je veux extraire les données des documents scannés ou PDF afin de les structurer. | 8 | Élevée |
| Module Extraction documentaire | Classification automatique | 18 | En tant que système, je classe automatiquement le type de document afin de router le traitement. | 5 | Élevée |
| Module Extraction documentaire | Extraction NLP des champs | 19 | En tant que responsable environnement, je veux extraire les champs pertinents (montants, quantités, dates, unités, fournisseurs) afin de gagner du temps. | 8 | Élevée |
| Module Extraction documentaire | Validation humaine | 20 | En tant qu'utilisateur, je veux valider ou corriger les extractions afin de garantir leur fiabilité. | 5 | Élevée |
| Module Data Processing & Qualité | Normalisation des unités | 21 | En tant que système, je normalise les unités (kWh, m³, tonnes, litres) afin d'harmoniser les données hétérogènes. | 5 | Élevée |
| Module Data Processing & Qualité | Contrôle qualité des données | 22 | En tant que système, je détecte les valeurs manquantes, aberrantes et les doublons afin d'alerter l'utilisateur. | 8 | Élevée |
| Module Data Processing & Qualité | Data mapping automatique | 23 | En tant que système, j'applique la correspondance source → modèle afin d'intégrer les données dans le référentiel. | 8 | Élevée |
| Module Data Processing & Qualité | Workflow de validation | 24 | En tant que responsable environnement, je valide les données avant leur intégration au référentiel officiel. | 5 | Moyenne |
| Module Data Processing & Qualité | Apprentissage progressif du mapping | 25 | En tant que système, j'apprends des corrections utilisateur afin d'améliorer le mapping. | 8 | Moyenne |
| Module Analytics & IA | Calcul des indicateurs environnementaux | 26 | En tant que responsable environnement, je consulte les indicateurs (énergie, eau, déchets) afin de piloter la performance. | 8 | Élevée |
| Module Analytics & IA | Calcul des émissions carbone | 27 | En tant que responsable environnement, je consulte les émissions carbone par scope afin de suivre la conformité. | 8 | Élevée |
| Module Analytics & IA | Assistant IA RAG | 28 | En tant qu'utilisateur, j'interroge les données en langage naturel afin d'obtenir des réponses fiables et sourcées. | 13 | Élevée |
| Module Analytics & IA | Historique des requêtes IA | 29 | En tant que responsable environnement, je consulte l'historique des requêtes IA afin de suivre les interrogations. | 3 | Moyenne |
| Module Restitution | Dashboard ESG | 30 | En tant que responsable environnement, je consulte le dashboard ESG afin de visualiser les indicateurs agrégés. | 8 | Élevée |
| Module Restitution | Rapports exportables | 31 | En tant que responsable environnement, j'exporte des rapports (ESG, BEGES, personnalisés) afin de les partager. | 5 | Moyenne |
| Module Infrastructure transverse | Déploiement conteneurisé (Docker) | 32 | En tant qu'admin, je déploie l'application via Docker afin de garantir la portabilité et la résilience. | 5 | Élevée |
| Module Infrastructure transverse | Documentation de l'API | 33 | En tant que développeur, je consulte la documentation Swagger de l'API afin d'intégrer les services. | 3 | Élevée |

**Tableau 2.1 : Le Backlog du produit**

### 2.3 Planification des Releases / Sprints

Nous avons choisi de diviser le projet en **4 Releases**, chacune livrant un incrément potentiellement livrable. Le tableau 2.2 indique les sprints, les modules traités et la durée de chacun.

| Release | Sprints | Modules (livrables) | Durée |
|---|---|---|---|
| Release 1 — Fondations & Sécurité | Sprint 1 | Module Authentification et gestion des profils | 3 semaines |
| Release 1 — Fondations & Sécurité | Sprint 2 | Module Modèle de données et référentiel multi-tenant | 3 semaines |
| Release 2 — Collecte & Intégration | Sprint 3 | Module Collecte : fichiers, API et SQL | 3 semaines |
| Release 2 — Collecte & Intégration | Sprint 4 | Module Connecteur ERP et data mapping | 3 semaines |
| Release 3 — Documentaire & Qualité | Sprint 5 | Module Extraction documentaire (OCR/NLP) | 3 semaines |
| Release 3 — Documentaire & Qualité | Sprint 6 | Module Qualité et normalisation des données | 3 semaines |
| Release 4 — Analytics & Restitution | Sprint 7 | Module Indicateurs et dashboard ESG | 3 semaines |
| Release 4 — Analytics & Restitution | Sprint 8 | Module Assistant IA (RAG) | 3 semaines |

**Tableau 2.2 : Planification des Releases / Sprints**

### 2.4 Environnement technologique

Les technologies retenues (selon le cahier des charges) sont présentées dans le tableau 2.3.

| Domaine | Technologie |
|---|---|
| Backend | FastAPI (Python) |
| Frontend | Next.js (React, TypeScript) |
| Base de données | PostgreSQL (extensions JSON, pgvector) |
| Intelligence artificielle | Python, LangChain, LLM, base vectorielle |
| OCR | Tesseract, PaddleOCR |
| Authentification | JWT, OAuth2, RBAC |
| Infrastructure | Docker, Kubernetes, Cloud (AWS/Azure/GCP) |

**Tableau 2.3 : Environnement technologique**

---

## Chapitre 3 : Backlogs des Sprints

Le terme « sprint » peut être défini comme une période de travail itérative permettant de produire un incrément potentiellement livrable. Dans ce chapitre, nous détaillons, pour chaque sprint, le **backlog du sprint** : les tâches à effectuer pour chaque user story, avec leur point d'effort.

### 3.1 Sprint 1 « Authentification et gestion des profils »

#### 3.1.1 Backlog du Sprint 1

Le tableau 3.1 définit les tâches à réaliser pour chaque user story du sprint 1. Ce sprint est **terminé** (backend FastAPI, frontend Next.js, 21 tests pytest, build et lint validés).

| ID | User Story | Tâche | Effort |
|---|---|---|---|
| 1 | En tant qu'utilisateur, je veux créer un compte afin d'accéder à mon espace. | Créer les modèles Company/User ; configurer l'endpoint REST /register ; créer la page d'inscription avec validation de formulaire. | 5 |
| 2 | En tant qu'utilisateur, je veux m'authentifier de manière sécurisée afin d'accéder à mon espace. | Hacher les mots de passe (bcrypt) ; émettre les jetons JWT (access + refresh) ; configurer l'endpoint /login ; créer la page de connexion. | 8 |
| 3 | En tant qu'utilisateur, je veux rafraîchir ma session afin de rester connecté. | Configurer l'endpoint /refresh avec rotation des jetons ; intégrer l'auto-refresh dans le client API frontend. | 5 |
| 4 | En tant qu'utilisateur, je veux me déconnecter afin de sécuriser mon poste. | Configurer l'endpoint /logout avec révocation du refresh token ; ajouter le bouton de déconnexion. | 3 |
| 5 | En tant que membre, je veux consulter mon profil afin de vérifier mes informations. | Configurer l'endpoint /me ; créer le dashboard affichant le profil utilisateur. | 3 |
| 6 | En tant qu'admin, je veux gérer les utilisateurs et leurs rôles afin de contrôler les accès. | Configurer le CRUD /users avec contrôle RBAC ; créer la page de gestion des utilisateurs (création, changement de rôle). | 8 |
| 7 | En tant qu'admin, je veux consulter le journal d'audit afin de tracer les actions sensibles. | Créer la table AuditLog ; journaliser les connexions, échecs et changements ; créer la page d'audit. | 5 |

**Tableau 3.1 : Backlog du Sprint 1**

### 3.2 Sprint 2 « Modèle de données et référentiel multi-tenant »

Le tableau 3.2 définit les tâches du sprint 2. Ce sprint est **terminé** (backend FastAPI, frontend Next.js, 51 tests pytest cumulés, build et lint validés).

| ID | User Story | Tâche | Effort |
|---|---|---|---|
| 8 | En tant qu'admin, je veux créer des sites industriels afin de structurer mes données par site. | Créer le modèle Site ; configurer le CRUD avec isolation tenant ; créer la page frontend des sites. | 5 |
| 9 | En tant qu'admin, je veux configurer des sources de données afin de préparer la collecte. | Créer le modèle DataSource ; configurer le CRUD ; créer la page frontend de configuration. | 5 |
| 10 | En tant que responsable, je veux consulter le référentiel des indicateurs afin de connaître le modèle de données. | Créer les tables indicateurs et émissions ; configurer les migrations de schéma (Alembic). | 5 |
| 11 | En tant qu'utilisateur, je veux saisir manuellement des données manquantes afin de compléter le référentiel. | Créer les formulaires de saisie manuelle avec identification des champs obligatoires. | 5 |
| 12 | En tant qu'admin, je veux que les données sensibles soient chiffrées afin de garantir leur sécurité. | Mettre en place le chiffrement AES-256 au repos et TLS en transit. | 5 |
| 13 | En tant qu'utilisateur, je veux renforcer ma connexion avec un code OTP afin de sécuriser l'accès. | Mettre en place la double authentification : challenge OTP au login, vérification anti-rejeu, activation/désactivation ; écran de connexion en 2 étapes. | 3 |

**Tableau 3.2 : Backlog du Sprint 2**

### 3.3 Sprint 3 « Collecte : fichiers, API et SQL »

Le tableau 3.3 définit les tâches du sprint 3.

| ID | User Story | Tâche | Effort |
|---|---|---|---|
| 14 | En tant que responsable environnement, je veux importer des fichiers Excel/CSV afin d'alimenter le référentiel. | Gérer l'upload des fichiers ; parser (pandas/openpyxl) ; afficher l'aperçu et le mapping des colonnes. | 8 |
| 15 | En tant que responsable environnement, je veux configurer une source API afin d'automatiser la collecte. | Créer le gestionnaire de connecteurs ; configurer OAuth2/clé API ; tester la connexion. | 8 |
| 16 | En tant que responsable environnement, je veux connecter une base SQL en lecture seule afin de collecter sans modification. | Configurer l'accès SQL en lecture seule (SQLAlchemy/ODBC) ; tester la connexion. | 8 |
| 17 | En tant qu'admin, je veux consulter les logs d'import afin de tracer les échanges. | Journaliser les imports (statut, volumétrie, durée) ; créer l'interface de consultation. | 5 |
| 18 | En tant que système, j'assure la reprise sur erreur afin de ne pas perdre de données. | Mettre en place les files de messages (RabbitMQ) et la reprise automatique. | 5 |

**Tableau 3.3 : Backlog du Sprint 3**

### 3.4 Sprint 4 « Connecteur ERP et data mapping »

Le tableau 3.4 définit les tâches du sprint 4.

| ID | User Story | Tâche | Effort |
|---|---|---|---|
| 19 | En tant que responsable environnement, je veux configurer une connexion ERP afin de préparer l'extraction. | Créer l'interface de configuration ; stocker les identifiants chiffrés (coffre-fort de secrets). | 8 |
| 20 | En tant que système, j'extrais les données via l'API native de l'ERP afin d'automatiser la collecte. | Développer le connecteur ERP type (Odoo) ; extraction en lecture seule stricte. | 13 |
| 21 | En tant que responsable environnement, je définis le mapping des champs source → modèle afin d'intégrer les données. | Développer le moteur de mapping configurable (product_qty → quantity, etc.). | 8 |
| 22 | En tant que responsable environnement, je planifie la synchronisation afin d'automatiser la collecte. | Configurer la planification (fréquence, périmètre, fenêtre horaire) avec APScheduler/Celery. | 5 |
| 23 | En tant que système, je détecte et gère les échecs de connexion afin d'alerter l'utilisateur. | Mettre en place le retry automatique, les alertes et le journal d'erreurs. | 5 |

**Tableau 3.4 : Backlog du Sprint 4**

### 3.5 Sprint 5 « Extraction documentaire (OCR/NLP) »

Le tableau 3.5 définit les tâches du sprint 5.

| ID | User Story | Tâche | Effort |
|---|---|---|---|
| 24 | En tant que responsable environnement, je veux déposer des documents afin de les traiter. | Créer la page de dépôt de documents (PDF, scans) ; stocker les Documents. | 5 |
| 25 | En tant que responsable environnement, je veux extraire les données des documents scannés afin de les structurer. | Développer le pipeline OCR (Tesseract/PaddleOCR) sur les documents scannés et PDF. | 8 |
| 26 | En tant que système, je classe automatiquement le type de document afin de router le traitement. | Développer la classification (facture énergie, bordereau, contrat, attestation). | 5 |
| 27 | En tant que responsable environnement, je veux extraire les champs pertinents des factures afin de gagner du temps. | Développer l'extraction NLP des champs (montants, quantités, dates, unités, fournisseurs). | 8 |
| 28 | En tant qu'utilisateur, je veux valider ou corriger les extractions afin de garantir leur fiabilité. | Créer l'interface de validation/correction humaine avant intégration. | 5 |

**Tableau 3.5 : Backlog du Sprint 5**

### 3.6 Sprint 6 « Qualité et normalisation des données »

Le tableau 3.6 définit les tâches du sprint 6.

| ID | User Story | Tâche | Effort |
|---|---|---|---|
| 29 | En tant que système, je normalise les unités afin d'harmoniser les données hétérogènes. | Développer le moteur de conversion des unités (kWh, m³, tonnes, litres). | 5 |
| 30 | En tant que système, je détecte les valeurs manquantes, aberrantes et les doublons afin d'alerter l'utilisateur. | Développer les règles de contrôle qualité et la détection d'anomalies. | 8 |
| 31 | En tant que responsable environnement, je reçois des alertes qualité afin de corriger rapidement. | Mettre en place le système d'alertes (valeur hors plage, incohérence temporelle, doublon). | 5 |
| 32 | En tant que responsable environnement, je valide les données avant leur intégration au référentiel officiel. | Développer le workflow de validation utilisateur. | 5 |
| 33 | En tant que système, j'apprends des corrections utilisateur afin d'améliorer le mapping. | Mettre en place l'apprentissage progressif du mapping. | 8 |

**Tableau 3.6 : Backlog du Sprint 6**

### 3.7 Sprint 7 « Indicateurs et dashboard ESG »

Le tableau 3.7 définit les tâches du sprint 7.

| ID | User Story | Tâche | Effort |
|---|---|---|---|
| 34 | En tant que responsable environnement, je consulte les indicateurs afin de piloter la performance. | Développer le calcul des indicateurs (énergie, eau, déchets) et les agrégations. | 8 |
| 35 | En tant que responsable environnement, je consulte les émissions carbone par scope afin de suivre la conformité. | Développer le calcul des émissions carbone (scopes 1, 2, 3). | 8 |
| 36 | En tant que responsable environnement, je consulte le dashboard ESG afin de visualiser les données. | Créer le dashboard ESG avec graphiques et comparaisons multi-sites. | 8 |
| 37 | En tant que responsable environnement, j'exporte des rapports afin de les partager. | Générer les rapports exportables (ESG, BEGES, personnalisés) en PDF/Excel. | 5 |

**Tableau 3.7 : Backlog du Sprint 7**

### 3.8 Sprint 8 « Assistant IA (RAG) »

Le tableau 3.8 définit les tâches du sprint 8.

| ID | User Story | Tâche | Effort |
|---|---|---|---|
| 38 | En tant que système, j'indexe les documents et les données afin de permettre la recherche sémantique. | Mettre en place l'indexation vectorielle (pgvector) dédiée par tenant. | 8 |
| 39 | En tant qu'utilisateur, j'interroge les données en langage naturel afin d'obtenir des réponses fiables. | Développer l'assistant conversationnel RAG (LangChain + LLM, recherche vectorielle + filtrage SQL). | 13 |
| 40 | En tant qu'utilisateur, je veux connaître les sources des réponses afin de vérifier leur fiabilité. | Implémenter la citation systématique des sources (document, indicateur, période). | 5 |
| 41 | En tant que responsable environnement, je consulte l'historique des requêtes IA afin de suivre les interrogations. | Créer la table AIQueries et l'interface d'historique. | 3 |

**Tableau 3.8 : Backlog du Sprint 8**

### 3.9 Récapitulatif des sprints

Le tableau 3.9 récapitule l'avancement des sprints.

| Sprint | Intitulé | Statut | Durée |
|---|---|---|---|
| Sprint 1 | Authentification et gestion des profils | Terminé | 3 semaines |
| Sprint 2 | Modèle de données et référentiel multi-tenant | Terminé | 3 semaines |
| Sprint 3 | Collecte : fichiers, API et SQL | Planifié | 3 semaines |
| Sprint 4 | Connecteur ERP et data mapping | Planifié | 3 semaines |
| Sprint 5 | Extraction documentaire (OCR/NLP) | Planifié | 3 semaines |
| Sprint 6 | Qualité et normalisation des données | Planifié | 3 semaines |
| Sprint 7 | Indicateurs et dashboard ESG | Planifié | 3 semaines |
| Sprint 8 | Assistant IA (RAG) | Planifié | 3 semaines |

**Tableau 3.9 : Récapitulatif des sprints**

---

## Conclusion générale

Dans ce document, nous avons présenté la gestion de projet agile du projet **SaaS Gestion Data** : le **Product Backlog** priorisé (33 fonctionnalités réparties en 7 modules), la **planification des Releases et des Sprints** (4 releases, 8 sprints de 3 semaines) ainsi que le **backlog détaillé de chaque sprint** avec les user stories, les tâches et les points d'effort. Les **Sprints 1 et 2** (authentification, gestion des profils, RBAC, multi-tenant, audit, référentiel de données et double authentification OTP) sont **terminés et livrables** : backend FastAPI, frontend Next.js, 51 tests automatisés cumulés, build et lint validés. Les sprints suivants permettront de livrer progressivement la collecte, le traitement documentaire, les indicateurs et l'assistant IA conformément au cahier des charges.

---

## Liste des abréviations

| Abréviation | Signification |
|---|---|
| SaaS | Software as a Service |
| JWT | Json Web Token |
| RBAC | Role-Based Access Control |
| RAG | Retrieval-Augmented Generation |
| API | Application Programming Interface |
| ERP | Enterprise Resource Planning |
| OCR | Optical Character Recognition |
| NLP | Natural Language Processing |
| SQL | Structured Query Language |
| ESG | Environnement, Social, Gouvernance |
| BEGES | Bilan d'Émissions de Gaz à Effet de Serre |
| IoT | Internet of Things |
| LLM | Large Language Model |
