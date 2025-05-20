Here's your completed `README.md` file — you can now copy-paste this directly into your repository:

```markdown
# Cloud File Service – Microservices Collaboration

This project is a **microservices-based cloud file storage system** built by **Rakai** and **Ken** as part of our learning journey. It follows a modular design where each contributor builds their services independently before integrating everything into a unified system.

---

## 🧱 Repository Structure

We have separated our services to work independently in the development phase:

```

cloud-file-service/
├── cloud-file-service-rakai/   ← Rakai's microservices
├── cloud-file-service-ken/     ← Ken's microservices
└── cloud-file-service-final/   ← Combined services (final integration)

````

Each contributor's folder contains their own:
- Backend services (e.g. metadata, block storage)
- Dockerfiles
- `.env` configurations
- `docker-compose.yml` for local orchestration

---

## 🔄 Integration Plan

Once both contributors finalize their own services:
1. We will move our stable services to `cloud-file-service-final/`.
2. Combine `docker-compose.yml` to orchestrate all services and databases.
3. Test inter-service communication, databases, and frontends as one system.

---

## 🔧 Tech Stack

- **FastAPI** for backend APIs
- **PostgreSQL** for metadata storage
- **Docker & Docker Compose** for containerization
- **Pydantic & SQLAlchemy** for models and ORM
- **Node.js/Express (planned)** for authentication (Ken)
- **MongoDB or S3 (planned)** for block storage

---

## 📦 How to Run (Dev)

Each service (e.g. Rakai’s metadata service) has its own `docker-compose.yml`.

To start a service:

```bash
cd cloud-file-service-rakai
docker-compose up --build
````

When integrated into `cloud-file-service-final/`, we will run:

```bash
cd cloud-file-service-final
docker-compose up --build
```

---

## 🚧 Work in Progress

We are still actively learning and developing:

* 🧠 Rakai is focusing on **metadata management & sync service**
* 🧠 Ken is focusing on **block storage & authentication**

Final integration will happen when both sides are stable.

---

## 🤝 Credits

* **Rakai Andaru Priandra**
* **Ken \[last name if you want to add]**

Special thanks to our lecturers, GitHub Copilot (sometimes 😅), Claude AI, DeepSeek, ChatGPT (that's a lot of AI), YouTube tutorials,
and all the StackOverflow legends.


