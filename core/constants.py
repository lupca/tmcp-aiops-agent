# HTTP Status Codes (Using typical SRE fallback strategies for Discord)
RETRY_STATUS_FORCELIST = [429, 500, 502, 503, 504]
DISCORD_HTTP_TIMEOUT_SECONDS = 10
DISCORD_MAX_RETRIES = 3
DISCORD_BACKOFF_FACTOR = 1

# Elasticsearch Query Constants
ES_FETCH_LOG_SIZE = 20
ES_DEFAULT_INDEX = "logs-*"

# App Metadata
APP_TITLE = "tmcp-aiops-agent"
APP_DESCRIPTION = "AIOps Automatic Root Cause Analysis API"

# Fallback values
DEFAULT_SERVICE_NAME = "unknown_service"

# Output Schema Formats
OLLAMA_RESPONSE_FORMAT = "json"
