import time
import logging
from fastapi import APIRouter, BackgroundTasks, Request
from typing import Dict
from workflow.graph import aiops_app
from core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# Deduplication cache
alert_cache: Dict[str, float] = {}

def run_aiops_workflow(payload: dict):
    """
    Executes the LangGraph workflow in the background.
    Protected with a broad exception handler to avoid crashing backend queue.
    """
    logger.info(f"Starting AIOps workflow background task for service: {payload.get('service_name')}")
    try:
        initial_state = {"alert_payload": payload, "surrounding_logs": "", "ai_analysis": {}}
        # Invoke the LangGraph pipeline
        aiops_app.invoke(initial_state)
        logger.info("AIOps workflow completed successfully.")
    except Exception as e:
        logger.error(f"AIOps workflow failed with an unexpected exception: {e}")

@router.post("/webhook/alert", status_code=200)
async def handle_alert_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Webhook endpoint to receive alerts from monitoring systems like Prometheus and Kibana.
    Responds immediately to avoid blocking the caller. Work is scheduled via BackgroundTasks.
    """
    try:
        data = await request.json()
    except Exception:
        return {"status": "error", "message": "Invalid JSON"}
        
    logger.info("Received alert webhook.")
    
    # 1. Prometheus Alertmanager Format Support
    if "alerts" in data:
        for alert in data["alerts"]:
            if alert.get("status") == "firing":
                service = alert.get("labels", {}).get("service", "unknown-service")
                error_msg = alert.get("annotations", {}).get("description", "No description")
                timestamp = alert.get("startsAt", str(time.time()))
                
                # Dedup
                now = time.time()
                if service in alert_cache and (now - alert_cache[service]) < settings.DEDUP_INTERVAL_SECONDS:
                    logger.info(f"Skipping duplicate Prometheus alert for {service}")
                    continue
                
                alert_cache[service] = now
                payload_dict = {
                    "service_name": service,
                    "timestamp": timestamp,
                    "error_message": error_msg
                }
                background_tasks.add_task(run_aiops_workflow, payload_dict)
                
    # 2. Classic Format Support
    else:
        service = data.get("service_name", "unknown-service")
        
        # Dedup
        now = time.time()
        if service in alert_cache and (now - alert_cache[service]) < settings.DEDUP_INTERVAL_SECONDS:
            logger.info(f"Skipping duplicate alert for {service}")
            return {"status": "skipped", "message": "Duplicate alert received recently."}
            
        alert_cache[service] = now
        background_tasks.add_task(run_aiops_workflow, data)
    
    return {
        "status": "success",
        "message": "Alert received. Background AI analysis initiated."
    }
