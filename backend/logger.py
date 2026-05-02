import logging
import sys

_logging_setup = False

def setup_logging():
    import config

    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )


def get_logger(name: str):
    if not _logging_setup:
        setup_logging()
    return logging.getLogger(name)