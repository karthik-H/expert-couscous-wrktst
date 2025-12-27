from apscheduler.schedulers.background import BackgroundScheduler
from .. import database, models
import datetime
import random
import logging

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

def fetch_energy_data():
    logger.info("Fetching energy data...")
    # Mock data fetch for now as endpoint is TBD
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Simulate network call
            generated = random.uniform(0, 100) # Mock value
            
            db = database.SessionLocal()
            try:
                data = models.EnergyData(
                    generated_energy=generated,
                    timestamp=datetime.datetime.utcnow()
                )
                db.add(data)
                db.commit()
                logger.info(f"Data saved: {generated:.2f} kWh")
                break # Success, exit retry loop
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                logger.error("Max retries reached. Data fetch failed.")

def start():
    # Schedule job every 1 minute
    scheduler.add_job(fetch_energy_data, 'interval', minutes=1)
    scheduler.start()

def shutdown():
    scheduler.shutdown()
