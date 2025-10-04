# UKNF Communication Platform (Django + Next.js)


Demonstration implementation of the UKNF communication and reporting platform. The stack aligns with the architectural guidelines: a Django REST backend providing the secure API surface and a React/Next.js 14 frontend delivering the operator UI. The solution covers the communication, authentication and administration modules described in `REQUIREMENTS.md` and `PROJECT_DETAILS.md`.


## Test Admin login 

```bash 
admin@example.com
Admin1234!
```


## Repository Structure

- `backend/` – Django 5 project with Django REST Framework. Implements custom user model, regulated entity directory, report workflow, secure messaging, announcements, audit logging, password policies, library API and GDPR-oriented utilities.
- `frontend/` – Next.js 14 application (App Router, TypeScript, Tailwind). Consumes the backend API, offers dashboards for reports, messaging, announcements, document library and self-service settings. Uses `knf_logo.png` in the global layout.
- `docker-compose.yml` – Production-leaning stack (backend, frontend, Postgres).
- `dev-docker-compose.yml` – Hot-reload oriented setup for local development.
- `REQUIREMENTS.md`, `PROJECT_DETAILS.md` – Source specifications.
- `DETAILS_UKNF_#Prompt2Code2.pdf` – Original supporting material.

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker (optional, for containerised workflow)

### Backend (Django)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py loaddata fixtures/seed_data.json  # optional demo data
python manage.py runserver
```

Key endpoints (default base: `http://localhost:8000/api`):

- `POST /auth/register` – Register external users
- `POST /auth/login` & `POST /auth/logout` – Obtain/clear auth tokens
- `GET /auth/profile` – User profile, memberships and acting entity
- `POST /auth/session` – Switch acting entity
- `GET/POST /auth/access-requests` – Manage onboarding flows
- `GET/POST /communication/reports` – Report lifecycle (submit/status)
- `GET/POST /communication/messages` – Secure messaging threads
- `GET/POST /communication/announcements` – Regulatory notices
- `GET /communication/library` & `GET /library/overview` – Document hub
- `GET/PUT /admin/password-policy` – Password hardening policies
- `GET /admin/audit-logs` – Immutable audit trail

### Frontend (Next.js)

```bash
cd frontend
npm install
npm run dev
```

Set `NEXT_PUBLIC_API_BASE_URL` to point at the backend (defaults to `http://localhost:8000/api`).

### Docker Workflow

Development containers with live reload:

```bash
docker compose -f dev-docker-compose.yml up --build
```

Production-style build (Gunicorn + Next.js build):

```bash
docker compose up --build
```

### Tests

```bash
cd backend
python manage.py test
```

(An initial auth integration test lives in `accounts/tests/test_auth.py`).

## Security & Compliance Features

- Token-based authentication, session context per acting entity
- Entity-scoped permissions with internal/external separation
- Comprehensive audit logging (`AuditLogEntry.record`) for sensitive actions
- Configurable password policy and notification preferences
- Report lifecycle states that mirror UKNF validation flow (draft → submitted → validated, etc.)
- Secure messaging with internal notes, announcements with acknowledgement tracking
- Library & FAQ modules exposing regulatory artefacts
- CORS, security headers and GDPR-friendly data retention models

## Accessibility & UX Highlights

- WCAG-friendly palette and focus states
- Responsive dashboard layout with quick access cards
- Status badges reflecting report validation states
- Forms with validation feedback (React Hook Form + Zod)
- Toast notifications for report actions (`sonner`)

## Next Steps

- Extend automated test coverage (API & frontend component tests)
- Integrate background workers for report validation pipelines
- Wire up SSO/identity provider for production environments
- Harden audit log persistence (append-only store) and add export tooling
