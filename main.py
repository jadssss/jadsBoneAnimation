# /main.py
# run this!!!

import core
import storage
import render
from gui import setup_gui
import logging

# DEBUG - full logs / полные логи
# INFO - only necessary logs / только необходимые логи
LOG_LEVEL = 'DEBUG'

# setup logging func
# инициализация логов
def setup_logging():
    level = getattr(logging, LOG_LEVEL)
    logging.basicConfig(level=level)

setup_logging()

logger = logging.getLogger(__name__)
logger.info("level logging is configured - %s", LOG_LEVEL)


try:
    logger.info("main.py start")
    scene = core.Scene()
    scene.Bone = core.Bone
    logger.info("scene initialized")
    setup_gui(scene, storage, render)
    logger.info("GUI is run")
except Exception as error:
    logger.error(f"main.py - {error}")