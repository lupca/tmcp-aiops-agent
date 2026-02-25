import logging
from fastapi import APIRouter, BackgroundTasks, Request, Depends
from api.services.alert_service import AlertService, get_alert_service

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/webhook/alert", status_code=200)
async def handle_alert_webhook(
    request: Request, 
    background_tasks: BackgroundTasks,
    alert_service: AlertService = Depends(get_alert_service)
):
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
        payloads = alert_service.process_prometheus_payload(data)
        for payload in payloads:
            background_tasks.add_task(alert_service.trigger_ai_workflow, payload)
                
    # 2. Classic Format Support
    else:
        payload = alert_service.process_classic_payload(data)
        if payload:
            background_tasks.add_task(alert_service.trigger_ai_workflow, payload)
        else:
            return {"status": "skipped", "message": "Duplicate alert received recently."}
    
    return {
        "status": "success",
        "message": "Alert received. Background AI analysis initiated."
    }

@router.post("/webhook/k8s-logs")
async def receive_fluentd_logs(
    request: Request, 
    background_tasks: BackgroundTasks,
    alert_service: AlertService = Depends(get_alert_service)
):
    """
    Endpoint hứng log dạng JSON array từ plugin out_http của Fluentd
    """
    try:
        data = await request.json()
    except Exception:
        return {"status": "error", "message": "Invalid JSON"}
    
    logger.info("Received k8s-logs webhook from Fluentd.")
    
    # Batch logging from Fluentd
    if isinstance(data, list):
        for log_entry in data:
            payload = alert_service.process_fluentd_payload(log_entry)
            if payload:
                background_tasks.add_task(alert_service.trigger_ai_workflow, payload)
    
    # Single log object
    elif isinstance(data, dict):
         payload = alert_service.process_fluentd_payload(data)
         if payload:
             background_tasks.add_task(alert_service.trigger_ai_workflow, payload)

    return {"status": "success", "message": "AIOps đã tiếp nhận tín hiệu k8s logs"}
