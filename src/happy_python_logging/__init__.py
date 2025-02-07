# SPDX-FileCopyrightText: 2025-present ftnext <takuyafjp+develop@gmail.com>
#
# SPDX-License-Identifier: MIT
import logging


def getLoggerForLibrary(name: str) -> logging.Logger:  # noqa: N802
    logger_for_library = logging.getLogger(name)
    logger_for_library.addHandler(logging.NullHandler())
    return logger_for_library
