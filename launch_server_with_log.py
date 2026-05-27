import uvicorn
import sys
import os

os.chdir(r'D:\www\法律大模型')

# Configure logging
logging_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(levelname)s - %(message)s"
        }
    },
    "handlers": {
        "file": {
            "class": "logging.FileHandler",
            "filename": "backend_error.log",
            "formatter": "default"
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["file"]
    }
}

uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False, log_config=logging_config)
