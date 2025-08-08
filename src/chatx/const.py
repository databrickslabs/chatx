import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv

# Log
logger = logging.getLogger(__name__)

# Env vars
load_dotenv()

DATABRICKS_HOST = os.getenv("DATABRICKS_HOST")
DATABRICKS_CLIENT_ID = os.getenv("DATABRICKS_CLIENT_ID")
DATABRICKS_CLIENT_SECRET = os.getenv("DATABRICKS_CLIENT_SECRET")
APP_ID = os.getenv("APP_ID", "")
APP_PASSWORD = os.getenv("APP_PASSWORD", "")
OAUTH_CONNECTION_NAME = os.getenv("OAUTH_CONNECTION_NAME", "")
WELCOME_MESSAGE = "Welcome to the Data Query Bot!"
WAITING_MESSAGE = "Querying Genie for results..."
SWITCHING_MESSAGE = "switch to @"
AUTH_METHOD = "oauth"  # can also be "service_principal"

# Spaces mapping in json file
__dir = Path(__file__).parent

with open(f"{__dir}/spaces.json") as f:
    SPACES = json.load(f)
REVERSE_SPACES = {v: k for k, v in SPACES.items()}
LIST_SPACES = ", ".join([f"@{space_name}" for space_name in SPACES.keys()])
SPACE_NOT_FOUND = (
    f"Genie space not found. Please use {LIST_SPACES} to specify the space."
)

TOKEN_EXPIRED_MESSAGE = "Oops, your token seems to have expired, please complete login process again."