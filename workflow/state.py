from typing import TypedDict, Any, Dict

class AlertState(TypedDict):
    alert_payload: Dict[str, Any]
    surrounding_logs: str
    ai_analysis: Dict[str, str]
