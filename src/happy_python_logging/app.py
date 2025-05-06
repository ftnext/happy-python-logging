import logging


def configureLogger(name: str, **kwargs) -> logging.Logger:
    logger = logging.getLogger(name)

    level = kwargs.pop("level", None)
    if level is not None:
        logger.setLevel(level)

    stream = kwargs.pop("stream", None)
    console_handler = logging.StreamHandler(stream)

    format = kwargs.pop("format", None)
    formatter = logging.Formatter(format)
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    return logger
