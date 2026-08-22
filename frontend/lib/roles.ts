import type {
  AuditAction,
  IndicatorCategory,
  Role,
  SourceType,
} from "./types";

export const ROLE_LABELS: Record<Role, string> = {
  admin: "Administrateur",
  responsable_environnement: "Responsable environnement",
  consultant: "Consultant",
  lecture_seule: "Lecture seule",
};

export const ROLE_OPTIONS: Role[] = [
  "admin",
  "responsable_environnement",
  "consultant",
  "lecture_seule",
];

export const AUDIT_ACTION_LABELS: Record<AuditAction, string> = {
  register: "Inscription",
  login: "Connexion",
  login_failed: "Échec de connexion",
  logout: "Déconnexion",
  refresh: "Rafraîchissement de session",
  password_change: "Changement de mot de passe",
  user_role_change: "Changement de rôle",
  otp_sent: "Code OTP envoyé",
  otp_verify_failed: "Échec de vérification OTP",
  otp_enabled: "Double authentification activée",
  otp_disabled: "Double authentification désactivée",
  site_created: "Création de site",
  site_updated: "Modification de site",
  site_deleted: "Suppression de site",
  data_source_created: "Création de source de données",
  data_source_updated: "Modification de source de données",
  data_source_deleted: "Suppression de source de données",
  indicator_created: "Création d'indicateur",
  data_created: "Saisie de donnée",
  data_updated: "Modification de donnée",
  data_validated: "Validation de donnée",
  import_previewed: "Prévisualisation d'import",
  import_committed: "Intégration d'import",
  mapping_saved: "Mapping enregistré",
  sync_scheduled: "Synchronisation planifiée",
  sync_run: "Synchronisation lancée",
  document_extracted: "Extraction documentaire",
  document_validated: "Validation documentaire",
};

export const SOURCE_TYPE_LABELS: Record<SourceType, string> = {
  csv: "Fichier CSV",
  excel: "Fichier Excel",
  api: "API",
  sql: "Base SQL",
  erp: "ERP",
  iot: "Capteurs IoT",
};

export const INDICATOR_CATEGORY_LABELS: Record<IndicatorCategory, string> = {
  energie: "Énergie",
  eau: "Eau",
  dechets: "Déchets",
  emissions: "Émissions",
  matieres: "Matières",
};
