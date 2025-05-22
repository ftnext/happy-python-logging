"""Example demonstrating file logging with happy_python_logging."""

import logging
import os
from happy_python_logging.app import configureLogger

# Configure a logger that writes to a file
log_file = "app.log"
logger = configureLogger(
    "file_example",
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)s | %(name)s - %(message)s",
    filename=log_file,
)

# Log some messages
logger.debug("This is a debug message")
logger.info("This is an info message")
logger.warning("This is a warning message")
logger.error("This is an error message")

# Show that the log file was created
print(f"Log file created at: {os.path.abspath(log_file)}")
print("Log file contents:")
with open(log_file, "r") as f:
    print(f.read())

# Clean up
os.remove(log_file)
print("Log file removed.")