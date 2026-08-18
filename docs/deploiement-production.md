# Déploiement production

Ce projet peut être présenté en démonstration maintenant, mais pour ouvrir l'accès à de vrais utilisateurs il faut le déployer avec une configuration production stricte.

## Avant de déployer

- Change le mot de passe Gmail normal si tu l'as partagé dans une conversation.
- Utilise uniquement un mot de passe d'application Gmail pour `SMTP_PASSWORD`.
- Ne mets jamais `backend/.env`, `frontend/.env.local` ou de vrais secrets dans Git.
- Garde `DEMO_MODE=false` et `OTP_EXPOSE_DEMO_CODE=false`.
- Utilise une base PostgreSQL durable, pas une base locale temporaire.
- Active HTTPS sur le frontend et le backend.

## Variables backend

Copie `backend/.env.production.example` vers `backend/.env.production`, puis remplace toutes les valeurs `CHANGE_ME`.

Variables importantes :

- `DATABASE_URL` : URL PostgreSQL production.
- `CORS_ALLOWED_ORIGINS` : URL HTTPS du frontend, par exemple `https://app.mondomaine.com`.
- `JWT_SECRET_KEY` : secret long et aléatoire pour les sessions.
- `DATA_ENCRYPTION_KEY` : secret long et aléatoire pour le chiffrement local.
- `SMTP_PASSWORD` : mot de passe d'application Gmail.
- `EMAIL_VERIFICATION_REQUIRED=true` : l'utilisateur doit confirmer son e-mail après inscription.

Générer un secret depuis PowerShell :

```powershell
[Convert]::ToBase64String([Security.Cryptography.RandomNumberGenerator]::GetBytes(48))
```

## Variables frontend

Copie `frontend/.env.production.example` vers `frontend/.env.production`.

Exemple :

```env
NEXT_PUBLIC_API_URL=https://api.mondomaine.com/api/v1
```

## Option VPS avec Docker Compose

Copie `.env.production.example` vers `.env.production` à la racine, remplace les valeurs `CHANGE_ME`, puis lance :

```powershell
docker compose --env-file .env.production -f docker-compose.prod.yml up -d --build
```

Vérifications après lancement :

- `https://api.mondomaine.com/health` retourne `status: ok`.
- L'inscription et la connexion fonctionnent.
- Le code OTP arrive par e-mail.
- Le dashboard charge les données sans erreur CORS.

## Option simple pour un PFE

- Frontend : Vercel.
- Backend : Render, Railway ou un VPS Docker.
- Base de données : PostgreSQL managé.
- Variables : configurer les mêmes variables production dans chaque plateforme.

## Checklist finale

- Secrets forts générés.
- Gmail App Password configuré.
- HTTPS activé.
- Domaine frontend ajouté dans `CORS_ALLOWED_ORIGINS`.
- `NEXT_PUBLIC_API_URL` pointe vers l'API réelle.
- `DEMO_MODE=false`.
- `OTP_EXPOSE_DEMO_CODE=false`.
- `EMAIL_VERIFICATION_REQUIRED=true`.
- Sauvegardes PostgreSQL activées.
- Tests backend et build frontend validés.
