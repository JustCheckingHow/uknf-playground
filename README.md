# UKNF Communication Platform (Django + React)


Demonstration implementation of the UKNF communication and reporting platform. The stack aligns with the architectural guidelines: a Django REST backend providing the secure API surface and a React 18 frontend (Vite) delivering the operator UI. The solution covers the communication, authentication and administration modules described in `REQUIREMENTS.md` and `PROJECT_DETAILS.md`.


## Test Admin login 

```bash 
admin@example.com
Admin1234!
```


## Repository Structure

- `backend/` – Django 5 project with Django REST Framework. Implements custom user model, regulated entity directory, report workflow, secure messaging, announcements, audit logging, password policies, library API and GDPR-oriented utilities.
- `frontend/` – React 18 single-page application built with Vite, TypeScript and Tailwind CSS. Consumes the backend API, offers dashboards for reports, messaging, announcements, document library and self-service settings. Uses `knf_logo.png` in the global layout.
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

API base URL (dev server): `http://localhost:8000/api`

API base URL (docker compose): `http://localhost:8123/api`

**Platform**
- `GET /health` – service heartbeat check.
- `GET /schema` & `GET /docs` – OpenAPI schema and Swagger UI backed by drf-spectacular.

**Authentication & Directory**
- `POST /auth/register` / `POST /auth/activate` – external onboarding and activation.
- `POST /auth/login` / `POST /auth/logout` – obtain or revoke a DRF token (`Authorization: Token <key>`).
- `GET /auth/profile` – authenticated user details, memberships and active session context.
- `POST /auth/session` – change the acting entity for multi-entity users.
- `GET/PUT /auth/preferences` – notification channel configuration.
- `GET /auth/roles` – role catalogue metadata used by the UI.
- `GET/POST /auth/entities` – regulated entity directory (mutations restricted to internal staff; `POST /auth/entities/{id}/verify` logs verifications).
- `GET/POST /auth/memberships` – entity membership management (entity admins can add/remove their members).
- `GET /auth/access-requests` – onboarding workflow, including `GET /auth/access-requests/my-active`, `POST /auth/access-requests/{id}/submit`, `POST /auth/access-requests/{id}/return`, `POST /auth/access-requests/{id}/lines/{line_id}/approve` and `POST /auth/access-requests/{id}/lines/{line_id}/block`.
- `GET/POST /auth/access-requests/{id}/messages` and `POST /auth/access-requests/{id}/attachments` – threaded discussions and supporting documents for access requests.
- `POST /auth/contacts` – public contact form; `GET /auth/contacts` exposes submissions to internal reviewers.
- `GET /auth/users` – internal user directory search (read-only).
- `GET/POST /auth/user-groups` – internal user groups for broadcast targeting (system admins only).

**Communication**
- `GET/POST /communication/reports` – report submissions and review (internal reviewers can invoke `POST /communication/reports/{id}/status`).
- `GET/POST /communication/cases` – supervisory case management (create/update/delete limited to UKNF staff).
- `GET/POST /communication/messages` – secure threads with `GET/POST /communication/messages/{id}/messages` for the conversation log and `POST /communication/messages/broadcast` for internal broadcasts.
- `GET/POST /communication/announcements` – regulatory announcements with `POST /communication/announcements/{id}/acknowledge` for receipt tracking.
- `GET /communication/library` – published regulatory resources.
- `GET /communication/faq` – active FAQ entries.

**Library**
- `GET /library/overview` – featured documents and FAQ highlights for the dashboard.
- `GET /library/search?q=` – full-text search over library documents.
- `POST /library/documents` / `DELETE /library/documents/{id}` – authenticated upload and removal of library artefacts.
- `POST /library/qa` – question-answering endpoint returning generated answers plus cited sources.

**Administration (internal)**
- `GET/PUT /admin/password-policy` – password policy configuration (system scope).
- `GET /admin/audit-logs` – searchable audit trail (internal-only).
- `GET/POST /admin/retention` – CRUD for data-retention policies keyed by `data_type`.
- `GET/POST /admin/maintenance` – maintenance window scheduling with audit logging.

### Frontend (React)

```bash
cd frontend
npm install
npm run dev
```

Set `VITE_API_BASE_URL` to point at the backend (defaults to `http://localhost:8000/api`).

### Docker Workflow

Development containers with live reload:

```bash
docker compose -f dev-docker-compose.yml up --build
```

Production-style build (Gunicorn + Vite build):

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
