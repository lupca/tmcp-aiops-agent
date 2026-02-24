# Log Context Error Messages
MSG_ES_NOT_INITIALIZED = "Elasticsearch client is not initialized. Cannot fetch logs."
MSG_ES_NO_LOGS_FOUND = "No logs found for this service in Elasticsearch."
MSG_ES_FETCH_ERROR = "Error fetching logs context from Elasticsearch: {}"
MSG_PENDING = "Pending"
MSG_NOT_PROVIDED = "Not provided."
MSG_ANALYSIS_PENDING = "Analysis pending."
MSG_NO_SUGGESTION = "No suggestion available."

# Discord Embedding Templates
DISCORD_USERNAME = "AIOps Alert Manager"
DISCORD_ALERT_TITLE = "🚨 Alert: {} failure detected"
DISCORD_COLOR_RED = 16711680
DISCORD_FOOTER_TEXT = "Powered by tmcp-aiops-agent"
DISCORD_FIELD_DESC = "Description"
DISCORD_FIELD_ROOT_CAUSE = "Root Cause Analysis (AI)"
DISCORD_FIELD_SUGGESTION = "Suggested Fix"

# AI Fallback Messages
LLM_FALLBACK_CAUSE = "LLM parsing/execution failed: {}"
LLM_FALLBACK_SOL = "Check connection to Ollama or review logs manually."
