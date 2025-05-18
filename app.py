import os
import uvicorn
from dotenv import load_dotenv
from multi_ai.api import app
from multi_ai.utils.helpers import create_default_env_file

# Load environment variables and create default .env file if needed
load_dotenv()
create_default_env_file()

# Server configuration
host = os.environ.get("HOST", "0.0.0.0")
port = int(os.environ.get("PORT", 8000))

if __name__ == "__main__":
    uvicorn.run(app, host=host, port=port)
