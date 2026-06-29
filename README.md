# Cairo Real-Time Traffic Enforcement Analytics Pipeline

## Overview

The Cairo Real-Time Traffic Enforcement Analytics Pipeline is an end-to-end cloud-based data engineering project that ingests, processes, and visualizes traffic enforcement data in real time.

The system retrieves JSON Lines traffic data from Microsoft Azure Blob Storage, normalizes and validates the incoming records, and presents live operational insights through an interactive Streamlit dashboard. It is designed to remain operational even when cloud connectivity or data quality issues occur by automatically switching to a local simulation mode.

---

## Features

* Real-time Azure Blob Storage ingestion
* JSON Lines parsing and validation
* Automatic schema recovery for missing fields
* Interactive Streamlit dashboard
* Vehicle type and traffic signal filtering
* Speed distribution analytics
* Geographical incident mapping
* License plate search
* Automatic incident logging
* Local simulation mode during Azure outages

---

## Project Architecture

```
Azure Blob Storage
│
├── violations (Summary JSONL)
└── output (Details JSONL)
          │
          ▼
 JSON Lines Parser
          │
          ▼
 Schema Validation
          │
          ▼
 Data Processing
          │
          ▼
 Streamlit Dashboard
          │
          ├── KPI Cards
          ├── Interactive Map
          ├── Charts
          ├── Data Tables
          └── Alert Logging
```

---

## Technologies Used

* Python
* Microsoft Azure Blob Storage
* Streamlit
* Pandas
* NumPy
* Plotly Express
* Azure Storage Blob SDK

---

## Project Structure

```
.
├── Dashboard/
|   ├── app.py
├── requirements.txt
├── README.md
├── Database_Setup/
│   ├── create_tables.sql
├── Stream_Analytics\
│   └── anomaly_detection.sql
├── Traffic_Project/Data_Simulator
|   └── traffic_generator.ipynp
├── .gitignore
└── screenshots/
```

---

## Installation

Clone the repository:

```bash
git clone https: https://github.com/sherif-ahmed1/Real-Time-Traffic-Analytics.git
```

Move into the project directory:

```bash
cd Real-Time-Traffic-Analytics
```

Install the required packages:

```bash
pip install -r requirements.txt
```

---

## Configuration

Create an Azure Storage Account and update the connection string inside the application:

```python
AZURE_CONNECTION_STRING = "DefaultEndpointsProtocol=https;AccountName=storagetraffic11;AccountKey=FndnvLfVm8RgEvB7S3vIPnmeM9ukN51X8F/GoDQWB6K8ZQwe1Ukm86WOVVOK4Qsd0ywelUYDtByH+ASt7EZRpA==;EndpointSuffix=core.windows.net"
```

Configure the required containers:

* violations
* output

---

## Running the Application

Start the Streamlit application:

```bash
python -m streamlit run app.py
```

The dashboard will be available at:

```
http://localhost:8501
```

---

## Dashboard Capabilities

The dashboard provides:

* Live traffic monitoring
* Vehicle speed analytics
* Violation distribution
* Traffic signal analysis
* Interactive filtering
* License plate lookup
* Geographical visualization
* Historical alert logs

---

## Error Handling

The application includes several fault-tolerance mechanisms:

* Missing JSON fields are automatically generated with fallback values.
* Azure connection failures trigger simulation mode.
* Empty datasets are handled gracefully.
* Runtime exceptions are logged without terminating the application.

---

## Future Improvements

* Machine learning for traffic prediction
* Historical data warehouse
* Real-time event streaming with Azure Event Hub
* User authentication and role management
* REST API for external integrations

---

## Team Members

* Project Manager / Lead Data Engineer : Feras Adel
* Data Pipeline Engineer : Mariam Marwan , Mohamed Hamed , Sherif Ahmed
* Data Analyst : Abdelrahman Samy , Kenzy Heasham 

---

## License

This project was developed for educational purposes as part of a Data Engineering course.
