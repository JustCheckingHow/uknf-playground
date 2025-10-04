# UKNF Communication Platform (Demo)

This repository hosts a demo implementation of the UKNF communication portal as described in the project requirements. It contains a Next.js 14 frontend and a NestJS backend, prepared for containerised development with docker-compose.

## Structure

- `frontend/` – Next.js 14 app router UI implementing the communication, reporting, FAQ, announcements, library and entities experiences.
- `backend/` – NestJS 10 REST API exposing demo endpoints for the communication, authentication and administration modules.
- `docker-compose.yml` – Local development orchestration for frontend, backend and the (currently unused) Postgres service.

## Quick start

```bash
# start the stack (requires Docker Desktop)
docker compose up --build
```

The compose file targets the dedicated `dev` stages in each Dockerfile and bind-mounts the project folders. That means source edits on the host are hot-reloaded inside the containers and Tailwind styles remain identical to a local `npm run dev` session.

Once the containers are running:
- Frontend: http://localhost:3000
- Backend API: http://localhost:4000/api
- Health check: http://localhost:4000/api/health

> **Tip**: The first start will run `npm install` inside the containers. Subsequent runs reuse the named `node_modules` and `.next` volumes for faster boot.

## Local development without Docker

You can run each app directly (requires Node.js 20+ installed locally).

```bash
# backend
cd backend
npm install
npm run start:dev

# frontend (in a separate terminal)
cd frontend
npm install
npm run dev -- --port 3000
```

> **Note**: Package installation requires internet access. If you are working offline snapshot dependency tarballs in advance or use a local registry mirror.

## API surface

- `GET /api/communication/reports` – demo report lifecycle data.
- `GET /api/communication/messages` – secure messaging threads.
- `GET /api/communication/cases` – regulatory case overview.
- `GET /api/communication/announcements` – announcements with acknowledgement rates.
- `GET /api/communication/library` – document metadata catalogue.
- `GET /api/communication/faq` – knowledge base entries.
- `GET /api/communication/entities` – supervised entities directory.
- `POST /api/auth/register` – register external users (in-memory demo).
- `POST /api/auth/access-requests` – submit access provisioning request.
- `POST /api/auth/session/:userId/entity` – select acting entity for the current session.
- `GET /api/admin/users` – internal user management sample.
- `GET /api/admin/roles` – role catalogue demo.
- `GET/PUT /api/admin/password-policy` – manage password requirements.

All endpoints respond with static demo data to showcase the contract that the frontend consumes.

## Prompt log

The file `prompts.md` in the repository root will contain the ordered list of prompts used to assemble the solution, as requested in the specification.
