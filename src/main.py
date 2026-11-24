from __future__ import annotations

import logging
import re
from urllib.parse import urljoin

from requests_cache import CachedSession
from tqdm import tqdm

from src.configs import configure_argument_parser, configure_logging
from src.constants import (
    BASE_DIR,
    DOWNLOADS_DIR_NAME,
    MAIN_DOC_URL,
    PEP_PYTHON_URL,
)
from src.exceptions import PageLoadException, ParserFindTagException
from src.outputs import control_output
from src.utils import find_tag, get_response, get_soup, parse_pep


def whats_new(session: CachedSession) -> list[tuple[str, str, str]]:
    """Собирает информацию о нововведениях в версиях Python."""
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')
    soup = get_soup(session, whats_new_url)

    main_div = find_tag(soup, 'section', {'id': 'what-s-new-in-python'})
    div_with_ul = find_tag(main_div, 'div', {'class': 'toctree-wrapper'})
    sections_by_python = div_with_ul.find_all(
        'li', attrs={'class': 'toctree-l1'}
    )

    results = [('Ссылка на статью', 'Заголовок', 'Редактор, автор')]
    errors = []

    for section in tqdm(sections_by_python):
        try:
            version_a_tag = find_tag(section, 'a')
            version_link = urljoin(whats_new_url, version_a_tag['href'])

            soup = get_soup(session, version_link)
            h1 = find_tag(soup, 'h1').text
            dl = find_tag(soup, 'dl')
            dl_text = dl.text.replace('\n', ' ')

        except (PageLoadException, ParserFindTagException) as error:
            errors.append(str(error))
            continue

        results.append((version_link, h1, dl_text))

    for error in errors:
        logging.warning(f'Не удалось обработать статью: {error}')

    return results


def latest_versions(session: CachedSession) -> list[tuple[str, str, str]]:
    """Собирает информацию о версиях Python и их статусах."""
    soup = get_soup(session, MAIN_DOC_URL)

    sidebar = find_tag(soup, 'div', {'class': 'sphinxsidebarwrapper'})
    ul_tags = sidebar.find_all('ul')

    for ul_tag in ul_tags:
        if 'All versions' in ul_tag.text:
            a_tags = ul_tag.find_all('a')
            break
    else:
        raise ParserFindTagException('Не найден список с версиями Python')

    results = [('Ссылка на документацию', 'Версия', 'Статус')]
    pattern = r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)'

    for a_tag in a_tags:
        match = re.search(pattern, a_tag.text)
        if match is not None:
            version, status = match.groups()
        else:
            version, status = a_tag.text, ''

        results.append((a_tag['href'], version, status))

    return results


def download(session: CachedSession) -> None:
    """Скачивает ZIP-архив HTML-документации Python."""
    downloads_url = urljoin(MAIN_DOC_URL, 'download.html')
    soup = get_soup(session, downloads_url)

    main_tag = find_tag(soup, 'div', {'role': 'main'})
    table_tag = find_tag(main_tag, 'table', {'class': 'docutils'})

    html_zip_tag = find_tag(
        table_tag,
        'a',
        {'href': re.compile(r'.+docs-html\.zip$')},
    )
    archive_url = urljoin(downloads_url, html_zip_tag['href'])
    response = get_response(session, archive_url)

    downloads_dir = BASE_DIR / DOWNLOADS_DIR_NAME
    downloads_dir.mkdir(exist_ok=True)

    filename = archive_url.split('/')[-1]
    archive_path = downloads_dir / filename

    with open(archive_path, 'wb') as file:
        file.write(response.content)

    logging.info(f'Архив был загружен и сохранён: {archive_path}')


def log_pep_results(
    skipped_rows: int,
    skipped_pep_zero: bool,
    errors: list[str],
    mismatches: list[str],
) -> None:
    """Записать результаты проверки PEP в лог."""
    if skipped_rows:
        logging.info(f'Пропущено строк без тега abbr: {skipped_rows}')

    if skipped_pep_zero:
        logging.info('PEP 0 пропущен.')

    for error in errors:
        logging.warning(f'Не удалось обработать PEP: {error}')

    for message in mismatches:
        logging.info(message)


def pep(session: CachedSession) -> list[tuple[str, str | int]]:
    """Собрать статистику статусов документов PEP."""
    statuses_dict = {}
    soup = get_soup(session, PEP_PYTHON_URL)
    pep_list = soup.find_all('tr', class_=['row-even', 'row-odd'])

    logging.info('Начата проверка статусов PEP.')

    skipped_rows = 0
    skipped_pep_zero = False
    errors = []
    mismatches = []

    for pep_tag in tqdm(pep_list):
        first_column_tag = pep_tag.find('abbr')
        if first_column_tag is None:
            skipped_rows += 1
            continue

        preview_status = first_column_tag.text[1:]

        try:
            link = find_tag(pep_tag, 'a', {'class': 'internal'})

            if link.text.strip() == '0':
                skipped_pep_zero = True
                continue

            link_url = urljoin(PEP_PYTHON_URL, link['href'])

            actual_status, mismatch = parse_pep(
                session, link_url, preview_status
            )
        except (PageLoadException, ParserFindTagException) as error:
            errors.append(str(error))
            continue

        statuses_dict[actual_status] = statuses_dict.get(actual_status, 0) + 1

        if mismatch is not None:
            mismatches.append(mismatch)

    log_pep_results(
        skipped_rows,
        skipped_pep_zero,
        errors,
        mismatches,
    )

    results = [('Статус', 'Количество')]
    results.extend(statuses_dict.items())
    total = sum(statuses_dict.values())
    results.append(('Total', total))

    return results


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
    'pep': pep,
}


def main() -> None:
    """Обрабатывает аргументы командной строки и запускает парсер."""
    try:
        configure_logging()
        logging.info('Парсер запущен!')

        arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
        args = arg_parser.parse_args()
        logging.info(f'Аргументы командной строки: {args}')

        session = CachedSession()
        if args.clear_cache:
            session.cache.clear()

        results = MODE_TO_FUNCTION[args.mode](session)

        if results is not None:
            control_output(results, args)

    except Exception:
        logging.exception('Ошибка при работе парсера.')

    logging.info('Парсер завершил работу.')


if __name__ == '__main__':
    main()
