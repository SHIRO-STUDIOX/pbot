import os
import sys
import logging
from logging.handlers import RotatingFileHandler

def setup_logger(log_level: str = "INFO", log_file_path: str = "logs/bot.log") -> logging.Logger:
    """
    Sets up a robust logging manager with console output formatting 
    and rotational file logging.
    """
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(log_file_path)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    # Convert log level string to logging constant
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO

    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Avoid duplicate handlers if already initialized
    if root_logger.handlers:
        return logging.getLogger("bot")

    # Define clean formatting
    log_format = logging.Formatter(
        "[%(asctime)s] %(levelname)-8s [%(name)s:%(filename)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console Handler (Stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    console_handler.setLevel(numeric_level)
    root_logger.addHandler(console_handler)

    # Rotating File Handler
    try:
        file_handler = RotatingFileHandler(
            log_file_path,
            maxBytes=5 * 1024 * 1024,  # 5 MB
            backupCount=3,
            encoding="utf-8"
        )
        file_handler.setFormatter(log_format)
        file_handler.setLevel(numeric_level)
        root_logger.addHandler(file_handler)
    except Exception as e:
        print(f"Failed to initialize rotating file handler: {e}", file=sys.stderr)

    logger = logging.getLogger("bot")
    logger.info("Logging successfully initialized. Level: %s", log_level.upper())
    return logger
