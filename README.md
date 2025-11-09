# Disaster Response Analytics – KPI Dashboard for Insurance Operations

>- Automated Ingestion and Analytics on disaster response data using Dockerized Data Pipelines and PostgreSQL.

## Background

**ResilienceWatch Analytics**, founded in 2015 in Berlin, Germany, specializes in real-time disaster impact analytics and predictive claims management for the insurance industry.  
In partnership with **SafeGuard Insurance**, one of Europe’s largest insurers, the company developed an automated analytics platform to enhance disaster recovery tracking and claims processing efficiency.  

The project leverages [**FEMA’s open APIs**](https://www.fema.gov/api/open/v2/PublicAssistanceFundedProjectsDetails) and integrates disaster and claims data into a unified analytics environment, enabling faster decision-making and improved customer response during crises.

### Project Overview 

The **Disaster Response KPI Dashboard** provides real-time insights into claims management and disaster recovery performance.  
It consolidates external disaster data (e.g., FEMA) and internal insurance claims data into a single PostgreSQL database for live KPI monitoring.

### **Business Challenge**

| **Challenge Area**                | **Description**                                                                                                | **Impact**                                                                      |
| --------------------------------- | -------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| **Lack of Real-Time Insights**    | Disaster recovery progress data is delayed or siloed, preventing timely decision-making during ongoing events. | Missed opportunities to allocate resources effectively and accelerate recovery. |
| **Inefficient Claims Processing** | Post-disaster claim volumes overwhelm manual processes, causing operational bottlenecks.                       | Slower payouts, customer frustration, and potential regulatory issues.          |
| **Fragmented Data Systems**       | Claims and disaster data are stored across separate, unconnected systems.                                      | Difficult to obtain a holistic view and prioritize claims intelligently.        |
| **Customer Experience Impact**    | Delays and lack of transparency during claims handling damage trust.                                           | Reduced satisfaction, loss of customer loyalty, and brand reputation risk.      |

### **Key Objectives**

- Centralized integration of disaster and claims data allowing for comprehensive tracking and reporting
- Real-time KPI dashboard for operational performannce monitoring and reporting
- Automated ETL pipeline deployment using continuous integration and continuous deployment (CI/CD) to
ensure that the disaster response platform is regularly updated with new features, enhancements, and data integrations

## Project Setup 

1. **Data Ingestion:** FEMA public APIs → Dockerized ETL pipeline → PostgreSQL  
2. **Processing:** Python scripts perform extraction, transformation, and loading (ETL).  
3. **Storage:** Central PostgreSQL database for disaster events, declarations, and claims.  
4. **Visualization:** Power BI / Tableau dashboards for KPI monitoring.  
5. **Automation:** CI/CD via GitHub Actions for container builds, tests, and deployments. 

### Technology Stack  

| Layer | Tools / Technologies |
|-------|-----------------------|
| **ETL & Analytics** | Python, Pandas, Requests |
| **Database** | PostgreSQL |
| **Containerization** | Docker, Docker Compose, Docker Registry |
| **Automation** | GitHub Actions (CI/CD) |
| **Visualization** | Power BI, Tableau |
| **Data Source** | FEMA Open Data APIs |

## Solution Architecture and Data Flow

![Disaster Response Data Pipeline](assets/disaster_pipeline.png)

### Simplified Data Flow

| **Step** | **Component**                 | **Description / Flow**                                                                                 |
| -------- | ----------------------------- | ------------------------------------------------------------------------------------------------------ |
| 1      | 🌐 **API Sources**            | FEMA & Weather APIs provide real-time disaster and declaration data →                                  |
| 2      | 🐍 **Python ETL**             | Extracts, transforms, and loads JSON data →                                                            |
| 3      | 🐳 **Docker & Compose**       | Containerized ETL pipeline ensures reproducible environments →                                         |
| 4      | 🐘 **PostgreSQL Database**    | Centralized storage for disaster & claims data →                                                       |
| 5      | 📊 **Power BI Dashboard**     | Connects to PostgreSQL for live KPI visualization →                                                    |
| 6       | 🧩 **GitHub Actions (CI/CD)** | Automates testing, building, and deployment → pushes Docker image to Registry → updates ETL containers |

### Repository Structure  

```bash
DisasterResponseAnalytics/
├── docker-compose.yml          # Defines multi-container setup (ETL + DB)
├── .env                        # Environment variables (API keys, DB creds)
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
│   └── Disaster_KPI.pbix       # Power BI / Tableau dashboard file
├── .github/
│   └── workflows/
│       └── ci_cd.yml           # Linting, build, and deploy automation
└── README.md                   # Project documentation
```

### Setup & run

>1. Clone repo and create the folders/files as above (or drop these into your existing project).
      ```bash
      git clone https://github.com/AnnieFiB/Disaster_Response_CI-CD
      ```
>2. Create .env
>3. How etl.py behaves
      ```ini
       - First run: landing is empty → full dump → then an incremental sweep using max(DB watermark, today@00:00Z) (today guard).
       - Subsequent runs: incremental only, using the stored DB MAX(lastrefresh)—but never earlier than today’s midnight on the first incremental day.
       - Scheduling: set POLL_ONCE=false and POLL_INTERVAL_SEC=86400 to run daily inside the container.
      ```
>4. Bring the stack up:
      ```bash
            docker compose up -d --build
            docker compose logs -f postgres # watch init scripts complete log
            docker compose logs -f etl      # watch landing/flat loads log
      ```
>5. For a redeployment:
        ```bash
            docker compose down -v          # removes containers + postgres_data volume
            docker volume ls | grep disaster-response-analytics
            docker volume rm volume-id
            docker compose up -d --build
      ```

```markdown
      | Step                        | Command                                              | Result                                         |
| --------------------------- | ---------------------------------------------------- | ---------------------------------------------- |
| Identify container’s volume | `docker ps --format "table {{.Names}}\t{{.Mounts}}"` | Finds the hash volume name                     |
| Remove that one volume      | `docker volume rm <volume-id>`                       | Deletes only this stack’s Postgres data        |
| Rebuild                     | `docker compose up -d --build`                       | Fresh FEMA ETL start, other projects untouched |

```

>6.Validate Postgres:
      >- pgAdmin → connect to Local-Postgres (already preconfigured), DB fema.
      >- Check table public.fema_pa_projects_v2 and view public.fema_pa_projects_v2_flat.
>7. Power BI Desktop
      >- Get Data → PostgreSQL database → Server: localhost, Database: fema (port 5434).
      >- Use fema_pa_projects_v2_flat for a flattened feed. Schedule refresh later via a gateway if you publish to Power BI Service.

### Summary workflow

| Step                           | Command                                                      | Description                                                      |
| ------------------------------ | ------------------------------------------------------------ | ---------------------------------------------------------------- |
| **1. Build & start services**  | `docker compose up -d --build`                               | Builds ETL container and initializes DB.                         |
| **2. Wait for DB healthcheck** | (auto)                                                       | Compose waits until Postgres is healthy.                         |
| **3. ETL runs**                | (auto)                                                       | `etl.py` starts, pulls FEMA API data, loads landing, syncs flat. |
| **4. Verify**                  | `docker exec -it dr_postgres psql -U admin -d fema -c "\dt"` | Confirm tables exist.                                            |
| **5. Connect Power BI**        | Host `localhost`, Port `5434`, Database `fema`               | Use `fema_pa_projects_v2_flat` as your main table.               |
