import logging
from fastapi import FastAPI
from api.routes import webhook
from core.exceptions import AIOpsException, aiops_exception_handler
from core.constants import APP_TITLE, APP_DESCRIPTION

# Configure logging at root level
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title=APP_TITLE, description=APP_DESCRIPTION)

# Register Custom Exception Handler
app.add_exception_handler(AIOpsException, aiops_exception_handler)

# Include Routers
app.include_router(webhook.router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
