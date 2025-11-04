import logging
from logging.handlers import TimedRotatingFileHandler
import sys


def set_logger(name=__name__, level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y:%M:%D %H:%M:%S'
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    file_handler = TimedRotatingFileHandler(
        filename='app.log',
        when='m',
        interval=15,
        backupCount=5,
        encoding=None,
        delay=False,
        utc=False,
        atTime=None
    )
    file_handler.setFormatter(formatter)

    # logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger



