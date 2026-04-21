# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Web UI:** Created frontend interface using React, TypeScript, and Vite, served via Nginx.
- **Auth Service:** Implemented authentication microservice (`auth-service`) using Python.
- **Main Service:** Implemented core business logic and mailer worker (`main-service`).
- **IO Service:** Implemented input/output microservice with PostgreSQL database integration (`io-service`).
- **Infrastructure:** Added Kubernetes configurations (Kind) for deploying apps.
- **API Gateway & Message Broker:** Added Kong API Gateway and RabbitMQ for service communication.
- **Observability & Management:** Integrated Grafana dashboards, Portainer, and Adminer.
- **CI/CD pipelines:** Added GitHub Actions workflows (`auth-service-cd.yml`, `io-service-cd.yml`, `main-service-cd.yml`, `web-ui-cd.yml`) for automated deployments.
- **Setup:** Created `start.sh` script for rapid cluster deployment.

[unreleased]: https://github.com/arthurpeter/Proiect_IDP
