#!/usr/bin/env python3.11

import logging
from pathlib import Path
import sys

def get_logger(name: str, log_file_path: Path, level=logging.INFO, file_level=logging.DEBUG, stream_level=logging.INFO) -> logging.Logger:
    # init logging.Logger object
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # setup formatter
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s', '%d-%m-%Y %H:%M:%S')

    # setup handlers

    # file handler
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(file_level)
    logger.addHandler(file_handler)

    # stream handler
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(stream_level)
    logger.addHandler(stream_handler)

    return logger
