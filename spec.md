# Project Specification

## 1. Overview
A web application for energy data collection, user onboarding, and monitoring.
Stack: Python (FastAPI), TypeScript (React), PostgreSQL.

## 2. Technical Requirements
### Backend
- **Framework**: Python / FastAPI
- **Database**: PostgreSQL
- **Scheduler**: Async scheduler (e.g., APScheduler or native asyncio + sleep) for periodic tasks.

### Frontend
- **Framework**: TypeScript / React (Vite recommended)
- **Styling**: Vanilla CSS (per system instructions)

## 3. Functional Requirements

### 3.1 Energy Data Collection
- **Requirement**: Fetch energy generation data from an external endpoint.
    - **Frequency**: Every 1 minute.
    - **Endpoint**: [TBD - Configurable via Environment Variable]
- **Storage**: Store timestamped energy data in the database.
- **Reliability**:
    - Automatically retry failed requests (3 attempts).
    - Log errors (standard logging).

### 3.2 User Onboarding
- **Registration**:
    - Users provide basic info (Name, Email, Password).
- **Document Submission**:
    - Picture of energy source (Optional).
    - Supporting documents (PDF/Image) (Optional).
    - **Storage**: Store all files locally under `onboardingdoc/{userid}`.
- **Validation**:
    - Validate file types (image/*, application/pdf).
    - Validate file size (limit: 5MB).
    - **Navigation**: Provide a link to the Home Page (Dashboard) to skip uploading.
- **Access Control**:
    - Allow access to the main dashboard even if documents are not uploaded.

### 3.3 Energy Monitoring
- **Dashboard**:
    - Display **current energy** generated.
- **History**:
    - View historical data in **table** or **chart** format.

## 4. Assumptions & Constraints
- **Energy Endpoint**: The URL and API key (if needed) will be provided via environment variables.
- **Auth**: Basic JWT authentication for user mapping.
- **Development**: Docker composition (optional but good practice) or local run scripts.
