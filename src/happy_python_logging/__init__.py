# SPDX-FileCopyrightText: 2025-present ftnext <takuyafjp+develop@gmail.com>
#
# SPDX-License-Identifier: MIT
import logging


def getLoggerForLibrary(name: str, with_handler: bool = True) -> logging.Logger:  # noqa: N802, FBT001, FBT002
    """Return a logger added a NullHandler.

    If you are developing a library, you should typically add a NullHandler only.
    See https://docs.python.org/3/howto/logging.html#configuring-logging-for-a-library

    Args:
        name: The name for the logger.
        with_handler: Whether to add a NullHandler to the logger. Defaults to True.

    Equivalent when with_handler=True::

        logging.getLogger(name).addHandler(logging.NullHandler())

    When with_handler=False, functionally equivalent to ``logging.getLogger(name)``.
    If no handler is added by the library user, the last resort handler is used.
    https://docs.python.org/3/howto/logging.html#what-happens-if-no-configuration-is-provided
    """
    logger_for_library = logging.getLogger(name)
    if with_handler:
        logger_for_library.addHandler(logging.NullHandler())
    return logger_for_library
