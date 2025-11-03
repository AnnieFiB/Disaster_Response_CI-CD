# Disaster Response Analytics – KPI Dashboard for Insurance Operations

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
├── etl/
│   ├── extract.py              # Fetch FEMA data
│   ├── transform.py            # Clean and normalize datasets
│   └── load.py                 # Load processed data into PostgreSQL
├── db/
│   └── schema.sql              # Table creation scripts
├── dashboards/
│   └── Disaster_KPI.pbix       # Power BI / Tableau dashboard file
├── .github/
│   └── workflows/
│       └── ci_cd.yml           # Linting, build, and deploy automation
└── README.md                   # Project documentation
