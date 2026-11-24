import logging
from argparse import ArgumentParser
from collections.abc import Iterable
from logging.handlers import RotatingFileHandler

from src.constants import (
    CLEAR_CACHE_HELP,
    DT_FORMAT,
    ENCODING,
    LOG_BACKUP_COUNT,
    LOG_DIR,
    LOG_FILE,
    LOG_FORMAT,
    LOG_MAX_BYTES,
    MODE_HELP,
    OUTPUT_CHOICES,
    OUTPUT_HELP,
    PARSER_DESCRIPTION,
)


def configure_argument_parser(
    available_modes: Iterable[str],
) -> ArgumentParser:
    """Настроить парсер аргументов командной строки."""
    parser = ArgumentParser(description=PARSER_DESCRIPTION)
    parser.add_argument(
        'mode',
        choices=available_modes,
        help=MODE_HELP,
    )
    parser.add_argument(
        '-c',
        '--clear-cache',
        action='store_true',
        help=CLEAR_CACHE_HELP,
    )
    parser.add_argument(
        '-o',
        '--output',
        choices=OUTPUT_CHOICES,
        help=OUTPUT_HELP,
    )
    return parser


def configure_logging() -> None:
    """Настроить запись логов в файл с ротацией и вывод в терминал."""
    LOG_DIR.mkdir(exist_ok=True)

    rotating_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding=ENCODING,
    )
    logging.basicConfig(
        datefmt=DT_FORMAT,
        format=LOG_FORMAT,
        level=logging.INFO,
        handlers=(rotating_handler, logging.StreamHandler()),
    )
