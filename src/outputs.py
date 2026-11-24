from __future__ import annotations

import argparse
import csv
import datetime as dt
import logging

from prettytable import PrettyTable

from src.constants import (
    BASE_DIR,
    DATETIME_FORMAT,
    ENCODING,
    FILE_DIALECT,
    FILE_OUTPUT,
    PRETTY_OUTPUT,
    RESULTS_DIR_NAME,
)


def default_output(
    results: list[tuple[str, str | int]],
    cli_args: argparse.Namespace | None = None,
) -> None:
    """Вывести результаты парсинга построчно в терминал."""
    for row in results:
        print(*row)


def pretty_output(
    results: list[tuple[str, str | int]],
    cli_args: argparse.Namespace | None = None,
) -> None:
    """Вывести результаты парсинга в виде таблицы PrettyTable."""
    table = PrettyTable()
    table.field_names = results[0]
    table.align = 'l'
    table.add_rows(results[1:])
    print(table)


def file_output(
    results: list[tuple[str, str | int]],
    cli_args: argparse.Namespace,
) -> None:
    """Сохранить результаты парсинга в CSV-файл."""
    results_dir = BASE_DIR / RESULTS_DIR_NAME
    results_dir.mkdir(exist_ok=True)
    now_formatted = dt.datetime.now().strftime(DATETIME_FORMAT)
    file_path = results_dir / f'{cli_args.mode}_{now_formatted}.csv'

    with open(file_path, 'w', encoding=ENCODING) as f:
        writer = csv.writer(f, dialect=FILE_DIALECT)
        writer.writerows(results)

    logging.info(f'Файл с результатами был сохранён: {file_path}')


OUTPUT_FUNCTIONS = {
    PRETTY_OUTPUT: pretty_output,
    FILE_OUTPUT: file_output,
    None: default_output,
}


def control_output(
    results: list[tuple[str, str | int]],
    cli_args: argparse.Namespace,
) -> None:
    """Выбрать способ вывода результатов парсинга."""

    OUTPUT_FUNCTIONS[cli_args.output](results, cli_args)
