import logging
from colorlog import ColoredFormatter
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
TODAY = datetime.today().strftime('%d-%m-%Y')
LOG_DIR = SCRIPT_DIR / 'logs'
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE_PATH = LOG_DIR / f'{TODAY}.log'

logger = logging.getLogger('main')
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(LOG_FILE_PATH)
stream_handler = logging.StreamHandler()
file_handler.setLevel(logging.DEBUG)
stream_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter('[%(asctime)s] [%(levelname)-7s]: %(message)s', datefmt='%d-%m-%Y %H:%M:%S')
stream_formatter = ColoredFormatter(
    '%(log_color)s[%(asctime)s] [%(levelname)-7s]: %(message)s%(reset)s',
    datefmt='%d-%m-%Y %H:%M:%S',
    log_colors={
        'DEBUG':    'white',
        'INFO':     'green',
        'WARNING':  'yellow',
        'ERROR':    'red',
        'CRITICAL': 'red,bg_white',
    })
file_handler.setFormatter(file_formatter)
stream_handler.setFormatter(stream_formatter)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)
