import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from core.config import settings
from core.constants import RETRY_STATUS_FORCELIST, DISCORD_MAX_RETRIES, DISCORD_BACKOFF_FACTOR, DISCORD_HTTP_TIMEOUT_SECONDS
from core.exceptions import DiscordWebhookError
from resources import strings

logger = logging.getLogger(__name__)

def send_discord_alert(service_name: str, description: str, root_cause: str, solution: str) -> bool:
    """
    Sends an embedded message to the configured Discord Webhook URL.
    """
    webhook_url = settings.DISCORD_WEBHOOK_URL
    if not webhook_url:
        logger.warning("DISCORD_WEBHOOK_URL is not set. Skipping Discord notification.")
        return False

    payload = {
        "username": strings.DISCORD_USERNAME,
        "embeds": [
            {
                "title": strings.DISCORD_ALERT_TITLE.format(service_name),
                "color": strings.DISCORD_COLOR_RED,
                "fields": [
                    {
                        "name": strings.DISCORD_FIELD_DESC,
                        "value": description or strings.MSG_NOT_PROVIDED,
                        "inline": False
                    },
                    {
                        "name": strings.DISCORD_FIELD_ROOT_CAUSE,
                        "value": root_cause or strings.MSG_ANALYSIS_PENDING,
                        "inline": False
                    },
                    {
                        "name": strings.DISCORD_FIELD_SUGGESTION,
                        "value": solution or strings.MSG_NO_SUGGESTION,
                        "inline": False
                    }
                ],
                "footer": {
                    "text": strings.DISCORD_FOOTER_TEXT
                }
            }
        ]
    }

    try:
        # Create a session with retry strategy for better resilience (AIOps/SRE best practice)
        session = requests.Session()
        retry_strategy = Retry(
            total=DISCORD_MAX_RETRIES,
            status_forcelist=RETRY_STATUS_FORCELIST,
            backoff_factor=DISCORD_BACKOFF_FACTOR
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        
        response = session.post(webhook_url, json=payload, timeout=DISCORD_HTTP_TIMEOUT_SECONDS)
        response.raise_for_status()
        logger.info("Successfully sent Discord webhook alert.")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send Discord alert webhook after retries: {e}")
        raise DiscordWebhookError(message=f"Discord Webhook API Error: {str(e)}")
