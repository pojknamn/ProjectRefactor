import os

from loguru import logger
if not os.getenv('TESTS'):
    logger.add("info.log", filter=lambda record: record["level"].name == "INFO")
    logger.add("error.log", filter=lambda record: record["level"].name == "ERROR")
    logger.add('all.log')

PROJECT_FOLDER = os.getenv('PROJECT_PATH')
PROJECT_REFACTOR_PATH = os.getenv('PROJECT_REFACTOR_PATH')
META_KEY_NAME = "'initial_url'"

