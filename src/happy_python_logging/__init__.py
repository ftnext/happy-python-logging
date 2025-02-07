# SPDX-FileCopyrightText: 2025-present ftnext <takuyafjp+develop@gmail.com>
#
# SPDX-License-Identifier: MIT
import logging


def getLoggerForLibrary(name: str) -> logging.Logger:  # noqa: N802
    """Return a logger added a NullHandler.

    If you are developing a library, you should add a NullHandler only.
    See https://docs.python.org/3/howto/logging.html#configuring-logging-for-a-library

    Equivalent::

        logging.getLogger(name).addHandler(logging.NullHandler())
    """
    logger_for_library = logging.getLogger(name)
    logger_for_library.addHandler(logging.NullHandler())
    return logger_for_library
