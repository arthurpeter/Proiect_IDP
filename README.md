# Remailder

**Remailder** is a cloud-native email scheduling platform built with a microservices architecture. Users can compose emails from pre-designed HTML templates, schedule them for future delivery, and track their sending history -- all through a modern web interface.

The project was developed as part of the **IDP (Introduction to Distributed Platforms)** course and covers the full lifecycle of a cloud-native application: from source code and containerization to orchestration, API gateway routing, observability, and automated CI/CD pipelines.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Microservices](#microservices)
  - [Auth Service](#auth-service)
  - [Main Service (Business Logic)](#main-service-business-logic)
  - [IO Service (Data Layer)](#io-service-data-layer)
  - [Web UI (Frontend)](#web-ui-frontend)
- [Infrastructure Components](#infrastructure-components)
- [Network Topology](#network-topology)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Deployment](#deployment)
  - [Local Deployment (Kind)](#local-deployment-kind)
  - [Home Server Deployment (k3d)](#home-server-deployment-k3d)
- [Accessing the Services](#accessing-the-services)
- [CI/CD Pipelines](#cicd-pipelines)
- [API Reference](#api-reference)
- [Docker Images](#docker-images)

---

## Architecture Overview

Remailder follows a layered microservices architecture deployed on a Kubernetes cluster (1 manager + 2 worker nodes). All inter-service communication is routed internally, while external traffic enters exclusively through the Kong API Gateway.

```
                    Internet
                       |
               +-------v--------+
               |   Kong Gateway |  (API Gateway - public-net)
               +---+--------+---+
                   |        |
          +--------v--+  +--v-----------+
          |   Auth    |  |    Main      |  (internal-net)
          |  Service  |  |   Service    |
          +--------+--+  +--+---------+-+
                   |         |         |
                   |    +----v----+    |
                   |    | RabbitMQ|    |
                   |    +---------+    |
                   |                   |
               +---v-------------------v---+
               |       IO Service          |  (data-net)
               +----------+---------------+
                          |
                   +------v------+
                   |  PostgreSQL  |
                   +-------------+

        +-------------+     +----------+
        | Frontend UI |     | Nginx    |  (public-net)
        | (React/Vite)|---->| Reverse  |
        +-------------+     | Proxy    |
                             +----------+
```

The frontend communicates with backend services through Nginx, which proxies `/api/*` requests to the Kong Gateway. Kong then routes them to the appropriate internal microservice based on path prefixes (`/auth/*`, `/main/*`).

---

## Microservices

### Auth Service

Handles user registration, login, and JWT-based authentication.

| Detail       | Value                                                |
|------------- |------------------------------------------------------|
| Language     | Python 3.12                                          |
| Framework    | FastAPI + Uvicorn                                    |
| Port         | 8002                                                 |
| Network      | internal-net                                         |

**Endpoints:**

| Method   | Path        | Description                        | Auth Required |
|----------|-------------|------------------------------------|---------------|
| `GET`    | `/health`   | Health check                       | No            |
| `POST`   | `/register` | Register a new user account        | No            |
| `POST`   | `/login`    | Authenticate and receive JWT token | No            |
| `GET`    | `/me`       | Get current user profile           | Yes (Bearer)  |
| `DELETE` | `/account`  | Delete the authenticated account   | Yes (Bearer)  |

**Key details:**
- Passwords are hashed using bcrypt (via `passlib`) before being sent to the IO Service for storage.
- JWT tokens are generated using `python-jose` with HS256 algorithm and a configurable expiration time.
- User data persistence is delegated to the IO Service via synchronous HTTP calls (`httpx`).

---

### Main Service (Business Logic)

Core service responsible for email scheduling, template management, and dispatching emails via SMTP.

| Detail       | Value                                          |
|------------- |------------------------------------------------|
| Language     | Python 3.12                                    |
| Framework    | FastAPI + Uvicorn                              |
| Port         | 8001                                           |
| Network      | internal-net                                   |

**Endpoints:**

| Method | Path         | Description                             | Auth Required |
|--------|--------------|-----------------------------------------|---------------|
| `GET`  | `/health`    | Health check                            | No            |
| `POST` | `/schedule`  | Schedule an email for future delivery   | Yes (Header)  |
| `GET`  | `/history`   | Retrieve email sending history          | Yes (Header)  |
| `GET`  | `/templates` | Get all available HTML email templates  | Yes (Bearer)  |

**Key details:**
- Uses the RabbitMQ **delayed message exchange** plugin (`x-delayed-message`) to schedule emails with millisecond precision.
- When a scheduled email's delay expires, a background worker consumes the message, sends the email via SMTP (Brevo relay), and publishes a status update back to the `db_tasks` queue.
- Provides 4 built-in HTML email templates: Modern Professional, Minimalist Clean, Bold Alert, and Elegant Soft.

---

### IO Service (Data Layer)

Manages all database interactions asynchronously. Acts as the single source of truth for user records and email logs.

| Detail       | Value                                           |
|------------- |-------------------------------------------------|
| Language     | Python 3.12                                     |
| Framework    | FastAPI + Uvicorn + SQLAlchemy (async)           |
| Port         | 8000                                            |
| Network      | data-net                                        |

**Endpoints:**

| Method   | Path              | Description                                |
|----------|-------------------|--------------------------------------------|
| `GET`    | `/health`         | Health check                               |
| `GET`    | `/health/db`      | Database connectivity check                |
| `POST`   | `/users`          | Create a new user record                   |
| `GET`    | `/users/{email}`  | Retrieve user by email (includes hash)     |
| `DELETE` | `/users/{email}`  | Delete user and cascade-delete all logs    |
| `GET`    | `/logs/{user_id}` | Retrieve email logs for a given user       |

**Key details:**
- Uses `asyncpg` as the async PostgreSQL driver with SQLAlchemy 2.0 ORM.
- Runs a background RabbitMQ consumer (`db_tasks` queue) that persists email log entries and updates their status (`pending` -> `sent` / `failed`) as reported by the Main Service worker.
- Database tables are auto-created on startup via SQLAlchemy's `metadata.create_all`.

**Database Schema:**

```
users                          email_logs
+----+--------+---------------+  +----+---------+-----------+---------+------------+--------------+
| id | email  | password_hash |  | id | id_user | recipient | subject | status     | scheduled_at |
+----+--------+---------------+  +----+---------+-----------+---------+------------+--------------+
                                        FK -> users.id (CASCADE)
```

---

### Web UI (Frontend)

Single-page application providing the user-facing interface.

| Detail       | Value                                      |
|------------- |--------------------------------------------|
| Language     | TypeScript                                 |
| Framework    | React 18 + Vite + React Router v6          |
| Served by    | Nginx (multi-stage Docker build)           |
| Port         | 80 (container) / 3001 (host)               |
| Network      | public-net                                 |

**Pages:**

| Route       | Page           | Description                                      |
|-------------|----------------|--------------------------------------------------|
| `/login`    | LoginPage      | User registration and login forms                |
| `/`         | DashboardPage  | Overview dashboard (protected)                   |
| `/schedule` | SchedulePage   | Compose and schedule emails with templates        |
| `/history`  | HistoryPage    | View email sending history with status tracking  |

**Key details:**
- Nginx acts as both a static file server and a reverse proxy, forwarding `/api/*` requests to the Kong Gateway at `kong-gateway:8000`.
- JWT tokens are stored in the React context (`AuthContext`) and attached to API requests as Bearer tokens.
- Protected routes redirect unauthenticated users to the login page.

---

## Infrastructure Components

| Component        | Technology       | Purpose                                         | Port  |
|------------------|------------------|--------------------------------------------------|-------|
| **API Gateway**  | Kong 3.9         | Routes external API traffic to internal services | 8443  |
| **Database**     | PostgreSQL       | Persistent storage for users and email logs      | 5432  |
| **DB Admin**     | Adminer          | Web-based database management utility            | 8080  |
| **Message Broker** | RabbitMQ       | Async communication and delayed email scheduling | 15672 |
| **Monitoring**   | Grafana + Prometheus + Loki | Observability stack with dashboards    | 3000  |
| **Log Aggregation** | Promtail + Loki | Centralized log collection from all pods       | --    |
| **Cluster Mgmt** | Portainer        | Web UI for Kubernetes cluster management         | 9000  |

---

## Network Topology

The cluster enforces network segmentation using Kubernetes `NetworkPolicy` resources. Services are separated into three distinct virtual networks:

| Network          | Components                                | Inbound Access From              |
|------------------|-------------------------------------------|----------------------------------|
| **public-net**   | Frontend UI, Kong Gateway                 | All traffic (internet-facing)    |
| **internal-net** | Auth Service, Main Service                | `public-net`, `internal-net`     |
| **data-net**     | IO Service, PostgreSQL, RabbitMQ          | `internal-net`, `data-net`       |

This ensures that the data layer is never directly accessible from the outside. All external requests must traverse the Kong Gateway and internal services before reaching the database or message broker.

---

## Technology Stack

| Layer            | Technologies                                                                  |
|------------------|-------------------------------------------------------------------------------|
| **Backend**      | Python 3.12, FastAPI, Uvicorn, SQLAlchemy 2.0, asyncpg, aio-pika, httpx      |
| **Frontend**     | TypeScript, React 18, Vite, React Router v6                                  |
| **Database**     | PostgreSQL (async via asyncpg)                                               |
| **Message Queue**| RabbitMQ (with delayed message exchange plugin)                               |
| **API Gateway**  | Kong 3.9 (DB-less / declarative mode)                                        |
| **Containerization** | Docker (multi-stage builds)                                              |
| **Orchestration**| Kubernetes (Kind for local / k3d for server deployment)                      |
| **CI/CD**        | GitHub Actions (automated Docker image builds on push to `main`)             |
| **Monitoring**   | Grafana, Prometheus, Loki, Promtail (deployed via Helm - loki-stack)         |
| **Management**   | Portainer, Adminer                                                           |
| **Web Server**   | Nginx (reverse proxy + SPA serving)                                          |
| **Email Relay**  | Brevo SMTP (transactional emails)                                            |

---

## Project Structure

```
Proiect_IDP/
├── .github/
│   └── workflows/
│       ├── auth-service-cd.yml       # CI/CD for auth-service
│       ├── io-service-cd.yml         # CI/CD for io-service
│       ├── main-sevice-cd.yml        # CI/CD for main-service
│       └── web-ui-cd.yml             # CI/CD for web-ui
├── kubernetes/
│   ├── apps/
│   │   ├── auth-deploy.yaml          # Auth Service deployment + service
│   │   ├── caddy-config.yaml         # Caddy TLS config (k3d)
│   │   ├── front-deploy.yaml         # Frontend deployment + service
│   │   ├── io-service.yaml           # IO Service deployment + service
│   │   └── main-service.yaml         # Main Service deployment + service
│   └── infra/
│       ├── adminer.yaml              # Adminer deployment
│       ├── dashboards/               # Grafana dashboard JSON configs
│       ├── kind-config.yaml          # Kind cluster config (1 CP + 2 Workers)
│       ├── kong-gateway.yaml         # Kong deployment + declarative config
│       ├── network-topology.yaml     # NetworkPolicies for network segmentation
│       ├── portainer.yaml            # Portainer deployment
│       ├── postgres-pvc.yaml         # PostgreSQL PersistentVolumeClaim
│       ├── postgres.yaml             # PostgreSQL deployment + service
│       └── rabbitmq.yaml             # RabbitMQ deployment + service
├── postman/
│   ├── io-service.postman_collection.json
│   └── main-service.postman_collection.json
├── src/
│   ├── auth-service/
│   │   ├── app/
│   │   │   ├── auth.py               # Password hashing + JWT utilities
│   │   │   ├── config.py             # Environment variable configuration
│   │   │   └── main.py               # FastAPI routes (register, login, me)
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── io-service/
│   │   ├── app/
│   │   │   ├── config.py             # Environment variable configuration
│   │   │   ├── database.py           # Async SQLAlchemy engine + session
│   │   │   ├── main.py               # FastAPI routes (users, logs, health)
│   │   │   ├── models.py             # SQLAlchemy ORM models (User, EmailLog)
│   │   │   └── worker.py             # RabbitMQ consumer for DB operations
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── main-service/
│   │   ├── app/
│   │   │   ├── config.py             # Environment variable configuration
│   │   │   ├── mailer.py             # SMTP email sending logic
│   │   │   ├── main.py               # FastAPI routes (schedule, history)
│   │   │   ├── templates.py          # HTML email template catalog
│   │   │   └── worker.py             # RabbitMQ consumer for email dispatch
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   └── web-ui/
│       ├── src/
│       │   ├── api.ts                # Typed API client for Kong Gateway
│       │   ├── App.tsx               # Router + protected routes
│       │   ├── AuthContext.tsx        # JWT auth context provider
│       │   ├── components/
│       │   │   └── Layout.tsx        # Sidebar navigation layout
│       │   ├── index.css             # Global styles
│       │   └── pages/
│       │       ├── DashboardPage.tsx  # Dashboard overview
│       │       ├── HistoryPage.tsx    # Email history table
│       │       ├── LoginPage.tsx      # Login / registration page
│       │       └── SchedulePage.tsx   # Email composer with templates
│       ├── Dockerfile                # Multi-stage build (Node -> Nginx)
│       ├── nginx.conf                # Nginx config (SPA + API proxy)
│       ├── package.json
│       └── vite.config.ts
├── .env                              # Environment variables (secrets)
├── .gitignore
├── CHANGELOG.md
├── start.sh                          # One-click local deployment (Kind)
└── start-k3d.sh                      # One-click server deployment (k3d)
```

---

## Prerequisites

- **Docker** (with the Docker daemon running)
- **kubectl**
- **Helm** (v3)
- **Kind** (for local deployment) or **k3d** (for server deployment)
- A `.env` file in the project root with the required environment variables (see `.env.example` or the provided `.env`)

All dependencies are automatically installed by the setup scripts if they are not already present on the system.

---

## Deployment

### Local Deployment (Kind)

The `start.sh` script handles everything automatically: installing missing tools, creating the Kubernetes cluster, deploying all manifests, installing the monitoring stack via Helm, and setting up port-forwarding.

```bash
chmod +x start.sh
./start.sh
```

The script will:
1. Detect the OS and package manager (apt/dnf)
2. Install Docker, kubectl, Kind, and Helm if not present
3. Create a Kind cluster with 1 control-plane and 2 worker nodes
4. Install the Loki monitoring stack (Grafana + Prometheus + Loki + Promtail) via Helm
5. Load pre-configured Grafana dashboards
6. Create Kubernetes secrets from the `.env` file
7. Apply all infrastructure and application manifests
8. Wait for all pods to become ready
9. Set up port-forwarding to localhost

### Home Server Deployment (k3d)

For deployment on a home server or any Linux machine with limited resources, use the `start-k3d.sh` script. It creates a k3d cluster (Kubernetes in Docker using k3s) and exposes services on all network interfaces (`0.0.0.0`), making them accessible from other devices on the local network.

```bash
chmod +x start-k3d.sh
./start-k3d.sh
```

This variant disables Traefik (since Kong is used as the API gateway) and optimizes Prometheus scrape intervals and retention for low-memory environments.

---

## Accessing the Services

After deployment, the following services are available:

| Service         | URL                     | Credentials                              |
|-----------------|-------------------------|------------------------------------------|
| Frontend UI     | `http://localhost:3001`  | Register a new account via the UI        |
| Kong Gateway    | `http://localhost:8443`  | --                                       |
| Grafana         | `http://localhost:3000`  | `admin` / (auto-generated, shown in terminal) |
| Adminer         | `http://localhost:8080`  | Server: `postgres-db`, User: `remailder_admin`, DB: `remailder_db` |
| Portainer       | `http://localhost:9000`  | Create admin account on first access     |
| RabbitMQ Mgmt   | `http://localhost:15672` | `guest` / `guest`                        |

---

## CI/CD Pipelines

Each microservice has a dedicated GitHub Actions workflow that automatically builds and pushes a new Docker image to Docker Hub whenever changes are pushed to the `main` branch in the corresponding source directory.

| Service       | Trigger Path               | Workflow File             |
|---------------|----------------------------|---------------------------|
| Auth Service  | `src/auth-service/**`      | `auth-service-cd.yml`     |
| IO Service    | `src/io-service/**`        | `io-service-cd.yml`       |
| Main Service  | `src/main-service/**`      | `main-sevice-cd.yml`      |
| Web UI        | `src/web-ui/**`            | `web-ui-cd.yml`           |

The workflows use `docker/build-push-action@v5` to build images from each service's `Dockerfile` and push them to Docker Hub under the `arthurp2003` namespace.

**Required GitHub Secrets:**
- `DOCKER_USERNAME` -- Docker Hub username
- `DOCKER_PASSWORD` -- Docker Hub access token

---

## API Reference

All API routes are exposed through the Kong Gateway. The frontend accesses them via the Nginx reverse proxy at `/api/*`.

**Kong Route Mapping:**

| Gateway Path | Target Service               | Target URL                     |
|------------- |------------------------------|--------------------------------|
| `/auth/*`    | Auth Service                 | `http://auth-service:8002`     |
| `/main/*`    | Main Service                 | `http://main-service:8001`     |

**Example: Schedule an email**

```bash
curl -X POST http://localhost:8443/main/schedule \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "X-User-Id: 1" \
  -d '{
    "to": "recipient@example.com",
    "subject": "Scheduled Email",
    "body": "<h1>Hello</h1><p>This was scheduled via Remailder.</p>",
    "scheduled_at": "2026-09-01T10:00:00Z",
    "is_html": true
  }'
```

---

## Docker Images

| Service       | Docker Hub Image                          |
|---------------|-------------------------------------------|
| Auth Service  | `arthurp2003/remailder-auth:latest`       |
| IO Service    | `arthurp2003/remailder-worker:latest`     |
| Main Service  | `arthurp2003/remailder-manager:latest`    |
| Web UI        | `arthurp2003/remailder-ui:latest`         |

---

## License

This project was developed for academic purposes as part of the IDP course at Politehnica University of Bucharest.