from happy_python_logging import getLoggerForLibrary

logger = getLoggerForLibrary(__name__)


def awesome():
    logger.info("想定通り")
    logger.warning("ちょっとヤバいよ")
