import logging
from typing import Dict, Any

from langgraph.graph import StateGraph, END
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

from core.config import settings
from core.constants import DEFAULT_SERVICE_NAME, OLLAMA_RESPONSE_FORMAT
from core.exceptions import ElasticsearchConnectionError, LLMAnalysisError, DiscordWebhookError
from core.es_client import get_surrounding_logs
from core.discord import send_discord_alert
from workflow.state import AlertState
from resources import prompts, strings

logger = logging.getLogger(__name__)

# Output Schema Validation
class AnalysisOutput(BaseModel):
    root_cause: str = Field(description="Short explanation of the root cause")
    solution: str = Field(description="Short actionable fix")

def fetch_logs_node(state: AlertState) -> Dict[str, Any]:
    """Node 1: Fetch surrounding logs using Elasticsearch."""
    payload = state.get("alert_payload", {})
    service_name = payload.get("service_name", DEFAULT_SERVICE_NAME)
    timestamp = payload.get("timestamp", "")
    
    logger.info(f"Node [fetch_logs_node]: Executing for {service_name} at timestamp {timestamp}")
    
    try:
        logs = get_surrounding_logs(service_name, timestamp)
    except ElasticsearchConnectionError as e:
        logger.error(f"Failed to fetch context logs: {e.message}")
        logs = e.message
        
    return {"surrounding_logs": logs}

def analyze_node(state: AlertState) -> Dict[str, Any]:
    """Node 2: Prompt LLM via Langchain to analyze errors using context."""
    payload = state.get("alert_payload", {})
    logs = state.get("surrounding_logs", strings.MSG_ES_NO_LOGS_FOUND)
    
    error_msg = payload.get("error_message", "Unknown error")
    
    # Init LLM connection pointing to Ollama model
    llm = ChatOllama(
        base_url=settings.OLLAMA_BASE_URL, 
        model=settings.OLLAMA_MODEL, 
        format=OLLAMA_RESPONSE_FORMAT, 
        temperature=0
    )
    
    parser = JsonOutputParser(pydantic_object=AnalysisOutput)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", prompts.SYS_PROMPT_ROOT_CAUSE),
        ("user", prompts.USER_PROMPT_ROOT_CAUSE)
    ])
    
    chain = prompt | llm | parser
    
    try:
        logger.info("Node [analyze_node]: Executing LLM analysis using Ollama...")
        analysis = chain.invoke({
            "error_msg": error_msg, 
            "logs": logs,
            "format_instructions": parser.get_format_instructions()
        })
    except Exception as e:
        logger.error(f"Error during LLM analysis: {e}")
        # Fallback handling in case LLM is unreachable or timeouts
        analysis = {
            "root_cause": strings.LLM_FALLBACK_CAUSE.format(str(e)),
            "solution": strings.LLM_FALLBACK_SOL
        }
    
    return {"ai_analysis": analysis}

def notify_node(state: AlertState) -> Dict[str, Any]:
    """Node 3: Build embed payload and send Discord notification."""
    payload = state.get("alert_payload", {})
    analysis = state.get("ai_analysis", {})
    
    logger.info(f"Node [notify_node]: AI Analysis result: {analysis}")
    
    service_name = payload.get("service_name", DEFAULT_SERVICE_NAME)
    description = str(payload.get("error_message", strings.MSG_NOT_PROVIDED))
    root_cause = str(analysis.get("root_cause", strings.MSG_PENDING))
    solution = str(analysis.get("solution", strings.MSG_PENDING))
    
    logger.info(f"Node [notify_node]: Sending notification to Discord for {service_name}")
    try:
        send_discord_alert(service_name, description, root_cause, solution)
    except DiscordWebhookError as e:
        logger.error(f"Discord notification failed fallback: {e.message}")
        
    return {}

def build_graph():
    """Compiles the LangGraph application."""
    workflow = StateGraph(AlertState)

    workflow.add_node("fetch_logs", fetch_logs_node)
    workflow.add_node("analyze", analyze_node)
    workflow.add_node("notify", notify_node)

    workflow.set_entry_point("fetch_logs")
    workflow.add_edge("fetch_logs", "analyze")
    workflow.add_edge("analyze", "notify")
    workflow.add_edge("notify", END)

    return workflow.compile()

# Public instance to be invoked by the API
aiops_app = build_graph()
