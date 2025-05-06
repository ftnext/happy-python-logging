"""Module to make logging happy for application developers."""

import io
import logging
from typing import TypedDict

from typing_extensions import Unpack


class LoggerConfiguration(TypedDict, total=False):
    level: int
    stream: io.TextIOWrapper
    format: str


def configureLogger(
    name: str, **kwargs: Unpack[LoggerConfiguration]
) -> logging.Logger:
    """Configure a non-root logger like `logging.basicConfig() <https://docs.python.org/ja/3/library/logging.html#logging.basicConfig>`__.

    Refer to https://rednafi.com/python/no_hijack_root_logger/

    Args:
        name (str): The name for the logger
        **kwargs: Optional configuration parameters
            level: The logging level (e.g., logging.INFO, logging.DEBUG)
            stream: The output stream (defaults to sys.stderr if None)
            format: The log message format string

    Returns:
        logging.Logger: A configured logger instance

    Example:
        >>> logger = configureLogger(
        ...     "awesome_lib",
        ...     level=logging.DEBUG,
        ...     format="%(asctime)s | %(levelname)s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
        ... )
        >>> logger.info("Application started")
    """
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
