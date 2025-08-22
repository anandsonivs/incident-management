"""Background worker for processing escalations and other periodic tasks."""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import logging
from typing import Optional

from app.db.session import SessionLocal
from app.services.escalation import get_escalation_service

logger = logging.getLogger(__name__)

class Worker:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.running = False
    
    async def start(self):
        """Start the background worker."""
        if self.running:
            logger.warning("Worker is already running")
            return
        
        logger.info("Starting background worker")
        
        # Add jobs
        self.scheduler.add_job(
            self.process_escalations,
            trigger=IntervalTrigger(minutes=1),  # Run every minute
            id="process_escalations",
            name="Process pending escalations",
            replace_existing=True,
            max_instances=1
        )
        
        # Start the scheduler
        self.scheduler.start()
        self.running = True
        logger.info("Background worker started")
    
    async def shutdown(self):
        """Shut down the background worker."""
        if not self.running:
            return
            
        logger.info("Shutting down background worker")
        self.scheduler.shutdown()
        self.running = False
        logger.info("Background worker stopped")
    
    async def process_escalations(self):
        """Process pending escalations."""
        db = SessionLocal()
        try:
            logger.info("Processing pending escalations")
            
            # Get escalation service
            escalation_service = get_escalation_service(db)
            
            # Get all active incidents that are not resolved or snoozed
            from app import crud
            from app.models.incident import IncidentStatus
            
            active_incidents = db.query(crud.incident.model).filter(
                crud.incident.model.status.notin_([
                    IncidentStatus.RESOLVED,
                    IncidentStatus.SNOOZED
                ])
            ).all()
            
            logger.info(f"Found {len(active_incidents)} active incidents to check for escalations")
            
            # Process each incident
            for incident in active_incidents:
                try:
                    await escalation_service.check_and_escalate_incident(incident)
                    db.commit()
                except Exception as e:
                    db.rollback()
                    logger.error(f"Error processing escalations for incident {incident.id}: {e}", exc_info=True)
            
            logger.info("Finished processing escalations")
            
        except Exception as e:
            logger.error(f"Error in escalation processing: {e}", exc_info=True)
            if db:
                db.rollback()
        finally:
            if db:
                db.close()

# Global worker instance
worker = Worker()

async def start_worker():
    """Start the background worker."""
    await worker.start()

async def stop_worker():
    """Stop the background worker."""
    await worker.shutdown()
