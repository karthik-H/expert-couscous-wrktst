# expert-couscous-wrktst
Testing codevalid workflow

# Software Requirement Specification

## 1. Tech Stack
- **Backend:** Python, FastAPI  
- **Frontend:** TypeScript, React  
- **Database:** PostgreSQL / MongoDB (for storing users and energy data)  
- **Others:** Cron or background task scheduler for periodic energy data fetching    

## 2. Functional Requirements
 
### 2.1 Energy Data Collection
- Fetch energy generation data from the provided endpoint **every 1 minute**.  
- Store timestamped energy data in the database.  
- Retry failed requests automatically and log errors.  
- validate and accept only if the energy data is in Mega watt hour units
### 2.2 User Onboarding
- Users can **register** with basic information.  
- During onboarding, users must submit:  
  - Picture of the energy source  
  - Supporting documents (PDF/image)  
  - Store all the files locally, under onboardingdoc/userid
- Validate uploaded files for type and size.  
- Uploading files is optional provide a link to  home page as well.

### 2.3 Energy Monitoring
- Home page displays **current energy generated** for the user’s energy source.  
- Allow users to view **historical energy data** in table or chart format.
