import logging
from elasticsearch import Elasticsearch
from core.config import settings
from core.constants import ES_FETCH_LOG_SIZE, ES_DEFAULT_INDEX
from core.exceptions import ElasticsearchConnectionError
from resources import strings

logger = logging.getLogger(__name__)

# Initialize Elasticsearch client safely
try:
    es = Elasticsearch(settings.ELASTICSEARCH_URL)
except Exception as e:
    logger.error(f"Failed to initialize Elasticsearch client: {e}")
    es = None

def get_surrounding_logs(service_name: str, timestamp: str, index: str = ES_DEFAULT_INDEX) -> str:
    """
    Queries Elasticsearch to get the last X logs for a given service.
    This acts as Context for the AI to analyze the alert.
    """
    if es is None:
        raise ElasticsearchConnectionError(message=strings.MSG_ES_NOT_INITIALIZED)
        
    try:
        # Construct query to fetch recent logs for the specific service
        query = {
            "size": ES_FETCH_LOG_SIZE,
            "sort": [{"@timestamp": {"order": "desc"}}],
            "query": {
                "bool": {
                    "must": [
                        {"match": {"service.name": service_name}}
                    ]
                }
            }
        }
        
        # Execute query (Note: In a real scenario, you can add timestamp range filters around `timestamp`)
        response = es.search(index=index, body=query)
        hits = response.get("hits", {}).get("hits", [])
        
        if not hits:
            return strings.MSG_ES_NO_LOGS_FOUND
            
        log_lines = []
        for hit in reversed(hits): # Reverse to get chronological order
            source = hit.get("_source", {})
            msg = source.get("message", "No message")
            ts = source.get("@timestamp", "No timestamp")
            log_level = source.get("log.level", "INFO")
            log_lines.append(f"[{ts}] [{log_level}] {msg}")
            
        return "\n".join(log_lines)
        
    except Exception as e:
        logger.error(f"Error fetching logs from Elasticsearch: {e}")
        raise ElasticsearchConnectionError(message=strings.MSG_ES_FETCH_ERROR.format(str(e)))
