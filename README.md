# Disaster Response Analytics – KPI Dashboard for Insurance Operations

> **Automated Ingestion and Analytics on disaster response data using Dockerized Data Pipelines and PostgreSQL.**

## Background

**ResilienceWatch Analytics**, founded in 2015 in Berlin, Germany, specializes in real-time disaster impact analytics and predictive claims management for the insurance industry.  
In partnership with **SafeGuard Insurance**, one of Europe’s largest insurers, the company developed an automated analytics platform to enhance disaster recovery tracking and claims processing efficiency.  

---

### Project Overview 

The **Disaster Response KPI Dashboard** provides real-time insights into claims management and disaster recovery performance.  
It consolidates external disaster data (e.g., FEMA) and internal insurance claims data into a single PostgreSQL database for live KPI monitoring.

---

### **Business Challenge**

| **Challenge Area**                | **Description**                                                                                                | **Impact**                                                                      |
| --------------------------------- | -------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| **Lack of Real-Time Insights**    | Disaster recovery progress data is delayed or siloed, preventing timely decision-making during ongoing events. | Missed opportunities to allocate resources effectively and accelerate recovery. |
| **Inefficient Claims Processing** | Post-disaster claim volumes overwhelm manual processes, causing operational bottlenecks.                       | Slower payouts, customer frustration, and potential regulatory issues.          |
| **Fragmented Data Systems**       | Claims and disaster data are stored across separate, unconnected systems.                                      | Difficult to obtain a holistic view and prioritize claims intelligently.        |
| **Customer Experience Impact**    | Delays and lack of transparency during claims handling damage trust.                                           | Reduced satisfaction, loss of customer loyalty, and brand reputation risk.      |

---

### **Key Objectives**

- Centralized integration of disaster and claims data allowing for comprehensive tracking and reporting
- Real-time KPI dashboard for operational performannce monitoring and reporting
- Automated ETL pipeline deployment using continuous integration and continuous deployment (CI/CD) to
ensure that the disaster response platform is regularly updated with new features, enhancements, and data integrations

---

## Data Source & Dictionary

The project leverages [**FEMA’s open APIs**](https://www.fema.gov/api/open/v2/PublicAssistanceFundedProjectsDetails) / [**FEMA’s Data Dictionary**](https://www.fema.gov/openfema-data-page/public-assistance-funded-projects-details-v2) and integrates disaster and claims data into a unified analytics environment, enabling faster decision-making and improved customer response during crises.

---

## Project Setup 

1. **Data Ingestion:** FEMA public APIs → Dockerized ETL pipeline → PostgreSQL  
2. **Processing:** Python scripts perform extraction, transformation, and loading (ETL).  
3. **Storage:** Central PostgreSQL database for disaster events, declarations, and claims.  
4. **Visualization:** Power BI / Tableau dashboards for KPI monitoring.  
5. **Automation:** CI/CD via GitHub Actions for container builds, tests, and deployments. 

---

### Technology Stack  

| Layer | Tools / Technologies |
|-------|-----------------------|
| **ETL & Analytics** | Python, Pandas, Requests |
| **Database** | PostgreSQL |
| **Containerization** | Docker, Docker Compose, Docker Registry |
| **Automation** | GitHub Actions (CI/CD) |
| **Visualization** | Power BI, Tableau |
| **Data Source** | FEMA Open Data APIs |

---

## Solution Architecture and Data Flow

![Disaster Response Data Pipeline](assets/disaster_pipeline.png)

---

### Simplified Data Flow

| **Step** | **Component**                 | **Description / Flow**                                                                                 |
| -------- | ----------------------------- | ------------------------------------------------------------------------------------------------------ |
| 1      | **API Sources**            | FEMA & Weather APIs provide real-time disaster and declaration data →                                  |
| 2      | **Python ETL**             | Extracts, transforms, and loads JSON data →                                                            |
| 3      | **Docker & Compose**       | Containerized ETL pipeline ensures reproducible environments →                                         |
| 4      | **PostgreSQL Database**    | Centralized storage for disaster & claims data →                                                       |
| 5      | **Power BI Dashboard**     | Connects to PostgreSQL for live KPI visualization →                                                    |
| 6       | **GitHub Actions (CI/CD)** | Automates testing, building, and deployment → pushes Docker image to Registry → updates ETL containers |

---

## Repository Structure  

```bash
DisasterResponseAnalytics/
├── docker-compose.yml          # Defines multi-container setup (ETL + DB)
├── compose.prod.yml           # Defines multi-container setup (etl Image from registry + DB)
├── .env                        # Environment variables (API keys, DB creds)
├── assets/                    # Images and others ...
├── db_init/                    # db, Table & index creation scripts
│   ├── 001_init.sql                             
│   └── 002_indexes.sql           
├── pgadmin/
│   └──servers.json             # servers creation scripts
├── etl/
│   ├── Dockerfile              
│   ├── requirements.txt          
│   └── etl.py                 # Fetch FEMA data, normalize & Load processed data into PostgreSQL     
├── dashboards/
│   ├── fema_blue.json        # Power BI theme
│   └── FEMA_Disaster_Response_Analytics.pbix       # Power BI / Tableau dashboard file
├── .github/
│   └── workflows/
│       └── ci-build-push.yml           # Automates building and pushing image.
└── README.md                   # Project documentation
```

---

## Deployment & Usage Guide

> **1. Clone the repo and create the folders/files as above**  
> *(or drop these into your existing project)*  
>
> ```bash
> git clone https://github.com/AnnieFiB/Disaster_Response_CI-CD
> ```

---

> **2. Create `.env`**  
> Include your environment variables (API URL, DB creds, scheduling interval, etc.)

---

> **3. How `etl.py` behaves**
>
> ```ini
> - First run: landing is empty → full dump → then an incremental sweep using max(DB watermark, today@00:00Z) (today guard).
> - Subsequent runs: incremental only, using the stored DB MAX(lastrefresh)—but never earlier than today’s midnight on the first incremental day.
> - Scheduling: set POLL_ONCE=false and POLL_INTERVAL_SEC=86400 to run daily inside the container.
> ```

---

> **4. Bring the stack up**
>
> ```bash
> docker compose up -d --build
> docker compose logs -f postgres   # watch init scripts complete
> docker compose logs -f etl        # watch landing/flat load logs
> ```

---

> **5. For a redeployment (clean start)**
>
> ```bash
> docker compose down -v                 # removes containers + postgres_data volume
> docker volume ls | grep disaster-response-analytics
> docker volume rm <volume-id>           # remove only this stack’s DB volume
> docker compose up -d --build
> ```
>
> | Step                        | Command                                              | Result                                         |
> | ---------------------------- | ---------------------------------------------------- | ---------------------------------------------- |
> | Identify container’s volume  | `docker ps --format "table {{.Names}}\t{{.Mounts}}"` | Finds the hash volume name                     |
> | Remove that one volume       | `docker volume rm <volume-id>`                       | Deletes only this stack’s Postgres data        |
> | Rebuild                      | `docker compose up -d --build`                       | Fresh FEMA ETL start, other projects untouched |

---

> **6. Validate Postgres**
>
> - Open **pgAdmin** → connect to *Local-Postgres* (already preconfigured).  
> - Verify database **`fema`**.  
> - Inspect tables:
>   - `public.fema_pa_projects_v2`
>   - `public.fema_pa_projects_v2_flat`
> 
> **On Local host**
>
> ```powershell
> psql -h 127.0.0.1 -p 5544 -U admin -d fema -c "select current_user, current_database();" 
> #if auth error (possibly on port; change port in compose or kill process listening on the port)
> ```

---

> **7. Power BI Desktop**
>
> - **Get Data → PostgreSQL database**  
>   - Server: `localhost`  
>   - Database: `fema`  
>   - Port: `5544` (if mapped from compose)  
> - Load table **`fema_pa_projects_v2_flat`** for a clean, flattened feed (Direct Query).  
> - When publishing to Power BI Service, configure a **Gateway** for scheduled refresh.

---

## Docker Image Publishing & Deployment Workflow

After verifying stack locally and connecting Power BI, you can publish your **ETL image** so it can run anywhere or be automatically deployed via CI/CD.

You have two options:

1. **Manual Local Push** — quick one-time upload to Docker Hub from your PC  
2. **Automated Push via GitHub Actions** — continuous builds to both GHCR and Docker Hub

---

### 🔹Manual Local Push to Docker Hub

Use this path first to confirm that your Docker build and authentication work.

#### **Prerequisites**

- Docker Desktop installed  
- Docker Hub account + access token with **Read & Write** scope  
  *(Account Settings → Security → New Access Token)*

#### **Steps**

```bash
# 1. Log in to Docker Hub (use the token as your password)
docker login

# 2. Build the ETL image locally
docker build -t disaster-response-etl:latest ./etl

# 3. Tag it for Docker Hub
docker tag disaster-response-etl:latest docker.io/<yourusername>/disaster-response-etl:latest

# 4. Push the image
docker push docker.io/<yourusername>/disaster-response-etl:latest

# 5. The image now appears in your Docker Hub account under
https://hub.docker.com/repository/docker/<yourusername>/disaster-response-etl.

# 6. Test the uploaded image
docker pull <yourusername>/disaster-response-etl:latest
docker run --rm <yourusername>/disaster-response-etl:latest
```

---

### Automated Push via GitHub Actions (CI/CD)

> Your repository contains a workflow (.github/workflows/ci-build-push.yml) that automatically builds and pushes the image to both registries when you push to main or create a release tag.

| Registry                             | Image Path                                          | Authentication                                    |
| ------------------------------------ | --------------------------------------------------- | ------------------------------------------------- |
| **GitHub Container Registry (GHCR)** | `ghcr.io/<username>/disaster-response-etl:latest`   | Built-in GitHub token                             |
| **Docker Hub**                       | `docker.io/<username>/disaster-response-etl:latest` | Secrets: `DOCKERHUB_USERNAME` + `DOCKERHUB_TOKEN` |

#### Setup

> - **On Docker Hub:**  
>   - Go to Account Settings → Security → New Access Token
>   - Choose Read & Write scope
>   - Copy the token
>
> - **On GitHub:**  
>   - Go to Settings → Secrets and variables → Actions

```ini
>   # Add to secrets: 
> DOCKERHUB_USERNAME : <your-dockerhub-username> 
> DOCKERHUB_TOKEN    : <your-access-token>

>   # Add to variables: in lowercase
> DOCKERHUB_USER: <your-dockerhub-username> 
> GHCR_OWNER: <your-github-username> 
> IMAGE_NAME: disaster-response-etl

# check docker connection with token from repo terminal
echo "dckr_pat_**** | docker login -u <username> --password-stdin
```

#### **Workflow Overview**  

```yaml
# .github/workflows/ci-build-push.yml (excerpt)

- name: Log in to GHCR
  uses: docker/login-action@v3
  with:
    registry: ghcr.io
    username: ${{ github.actor }}
    password: ${{ secrets.GITHUB_TOKEN }}

- name: Log in to Docker Hub
  uses: docker/login-action@v3
  with:
    username: ${{ secrets.DOCKERHUB_USERNAME }}
    password: ${{ secrets.DOCKERHUB_TOKEN }}

- name: Build and Push image
  uses: docker/build-push-action@v6
  with:
    context: ./etl
    file: ./etl/Dockerfile
    push: true
    tags: |
      ghcr.io/${{ github.repository_owner }}/disaster-response-etl:latest
      docker.io/${{ secrets.DOCKERHUB_USERNAME }}/disaster-response-etl:latest
```

**Pipeline behavior**
Every push to main or tag v*
      → builds ETL container
      → pushes it to GHCR + Docker Hub
      → tags it as latest (and versioned tag if applicable).

Verify builds
      - GitHub Actions: Repo → Actions → Build and Push Docker Image
      - GHCR: Repo → Packages tab
      - Docker Hub: hub.docker.com/repositories

---

#### **Using the Published Image**

Once published, reference the remote image in the deployment Compose file:

```yaml
# compose.prod.yml
services:
  etl:
    image: docker.io/<username>/disaster-response-etl:latest
    env_file: .env
    depends_on:
      postgres:
        condition: service_healthy
```

Then Deploy or update:

```bash
docker compose -f compose.prod.yml pull
docker compose -f compose.prod.yml up -d

# 2) Check health/logs
docker compose ps
docker compose logs -f etl
```

---

## Summary workflow

| Step                           | Command                                                                 | Description                                                                 |
| ------------------------------ | ----------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| **1. Build & start services**  | `docker compose up -d --build`                                          | Builds ETL container and initializes DB.                                   |
| **2. Wait for DB healthcheck** | (auto)                                                                  | Compose waits until Postgres is healthy.                                   |
| **3. ETL runs**                | (auto)                                                                  | `etl.py` starts, pulls FEMA API data, loads landing, syncs flat.           |
| **4. Verify**                  | `docker exec -it dr_postgres psql -U admin -d fema -c "\dt"`            | Confirm tables exist.                                                      |
| **5. Connect Power BI**        | Host `localhost`, Port `5544`, Database `fema`                          | Use `fema_pa_projects_v2_flat` as your main table.                         |
| **6. View pgAdmin dashboard**  | Open `http://localhost:5050` → login with `.env` credentials            | Inspect ETL logs, DB tables, and run SQL queries visually.                 |
| **7. Push to GHCR**            | `docker push ghcr.io/anniefib/disaster-response-etl:latest`             | Publishes image to GitHub Container Registry for CI/CD use.                |
| **8. Push to Docker Hub**      | `docker push docker.io/anniemona/disaster-response-etl:latest`          | Publishes the same ETL image for public or cross-platform deployment.      |
| **9. Stop all containers**     | `docker compose down`                                                   | Gracefully shuts down ETL, Postgres, and pgAdmin services.                 |
| **10. Clean environment**      | `docker volume rm disaster-response-analytics_postgres_data` *(optional)* | Removes Postgres data volume to start fresh or reclaim disk space.         |

---
