import time
import logging
from typing import Dict, List, Any
from core.config import settings
from workflow.graph import aiops_app

logger = logging.getLogger(__name__)

class AlertService:
    """
    Business logic layer for handling alerts and log streams.
    Isolates route handling from complex data parsing and deduplication.
    """
    def __init__(self):
        self.alert_cache: Dict[str, float] = {}

    def is_duplicate(self, service_name: str, dedup_interval: int = getattr(settings, 'DEDUP_INTERVAL_SECONDS', 300)) -> bool:
        """
        Check if an alert for a given service is a duplicate within the deduplication interval.
        """
        now = time.time()
        if service_name in self.alert_cache and (now - self.alert_cache[service_name]) < dedup_interval:
            return True
        
        self.alert_cache[service_name] = now
        return False

    def trigger_ai_workflow(self, payload: Dict[str, Any]) -> None:
        """
        Executes the LangGraph workflow in the background.
        Protected with a broad exception handler to avoid crashing the background task worker.
        """
        service_name = payload.get('service_name', 'unknown')
        logger.info(f"Starting AIOps workflow background task for service: {service_name}")
        try:
            initial_state = {"alert_payload": payload, "surrounding_logs": "", "ai_analysis": {}}
            # Invoke the LangGraph pipeline
            aiops_app.invoke(initial_state)
            logger.info("AIOps workflow completed successfully.")
        except Exception as e:
            logger.error(f"AIOps workflow failed with an unexpected exception: {e}")

    def process_prometheus_payload(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract standardized payloads from Prometheus Alertmanager format.
        """
        payloads = []
        if "alerts" not in data:
            return payloads
            
        for alert in data["alerts"]:
            if alert.get("status") == "firing":
                service = alert.get("labels", {}).get("service", "unknown-service")
                error_msg = alert.get("annotations", {}).get("description", "No description")
                timestamp = alert.get("startsAt", str(time.time()))
                
                if not self.is_duplicate(service):
                    payloads.append({
                        "service_name": service,
                        "timestamp": timestamp,
                        "error_message": error_msg
                    })
                else:
                    logger.info(f"Skipping duplicate Prometheus alert for {service}")
                    
        return payloads

    def process_classic_payload(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract standardized payload from a classic plain alert format.
        """
        service = data.get("service_name", "unknown-service")
        
        if self.is_duplicate(service):
            logger.info(f"Skipping duplicate alert for {service}")
            return {}
            
        return data

    def process_fluentd_payload(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract standardized payload from Fluentd Kubernetes log format.
        """
        namespace = log_data.get("kubernetes", {}).get("namespace_name", "unknown")
        pod_name = log_data.get("kubernetes", {}).get("pod_name", "unknown")
        error_msg = log_data.get("log", "")
        
        service_name = f"{namespace}/{pod_name}"
        logger.info(f"\n[AIOps Agent] Phân tích khẩn cấp từ {service_name}:")
        logger.info(f"Chi tiết lỗi: {error_msg}")
        
        # Return standardized payload
        return {
            "service_name": service_name,
            "timestamp": str(time.time()),
            "error_message": error_msg
        }

# Instantiate a singleton to preserve cache across requests
alert_service_instance = AlertService()

def get_alert_service() -> AlertService:
    """Dependency injection provider for FastAPI router"""
    return alert_service_instance
