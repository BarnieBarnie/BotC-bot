from pathlib import Path
from logger import logger

def load_token_from_file(file: Path) -> str:
    if not file.exists():
        logger.critical(f'{file} does not exist, either wrong path was specified or no token file exists')
        exit(1)
    logger.debug(f'Loading token from {file}')
    token = file.read_text()
    if token:
        logger.debug(f'Succesfully loaded token from {file}')
        return token
    logger.critical(f'Token file {file} seems to be empty, please add the token to the file')
    exit(1)
