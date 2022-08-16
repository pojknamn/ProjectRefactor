import os

from loguru import logger

logger.add("info.log", filter=lambda record: record["level"].name == "INFO")
logger.add("error.log", filter=lambda record: record["level"].name == "ERROR")
logger.add('all.log')

PROJECT_FOLDER = os.getenv('PROJECT_PATH')