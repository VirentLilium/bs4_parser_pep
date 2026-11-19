import logging
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from requests_cache import CachedSession
from tqdm import tqdm

from src.configs import configure_argument_parser, configure_logging
from src.constants import (
    BASE_DIR,
    EXPECTED_STATUS,
    MAIN_DOC_URL,
    PEP_PYTHON_URL,
)
from src.exceptions import ParserFindTagException
from src.outputs import control_output
from src.utils import find_tag, get_pep_status, get_response


def whats_new(session: CachedSession) -> list[tuple[str, str, str]] | None:
    """Собирает информацию о нововведениях в версиях Python."""
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')
    response = get_response(session, whats_new_url)
    if response is None:
        return

    soup = BeautifulSoup(response.text, features='lxml')
    main_div = find_tag(soup, 'section', {'id': 'what-s-new-in-python'})
    div_with_ul = find_tag(main_div, 'div', {'class': 'toctree-wrapper'})
    sections_by_python = div_with_ul.find_all(
        'li', attrs={'class': 'toctree-l1'}
    )

    results = [('Ссылка на статью', 'Заголовок', 'Редактор, автор')]

    for section in tqdm(sections_by_python):
        version_a_tag = find_tag(section, 'a')
        version_link = urljoin(whats_new_url, version_a_tag['href'])

        response = get_response(session, version_link)
        if response is None:
            continue

        soup = BeautifulSoup(response.text, 'lxml')
        h1 = find_tag(soup, 'h1').text
        dl = find_tag(soup, 'dl')
        dl_text = dl.text.replace('\n', ' ')
        results.append((version_link, h1, dl_text))

    return results


def latest_versions(
    session: CachedSession,
) -> list[tuple[str, str, str]] | None:
    """Собирает информацию о версиях Python и их статусах."""
    response = get_response(session, MAIN_DOC_URL)
    if response is None:
        return

    soup = BeautifulSoup(response.text, features='lxml')
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
    response = get_response(session, downloads_url)
    if response is None:
        return

    soup = BeautifulSoup(response.text, features='lxml')
    main_tag = find_tag(soup, 'div', {'role': 'main'})
    table_tag = find_tag(main_tag, 'table', {'class': 'docutils'})

    html_zip_tag = find_tag(
        table_tag,
        'a',
        {'href': re.compile(r'.+docs-html\.zip$')},
    )
    archive_url = urljoin(downloads_url, html_zip_tag['href'])

    response = get_response(session, archive_url)
    if response is None:
        return

    downloads_dir = BASE_DIR / 'downloads'
    downloads_dir.mkdir(exist_ok=True)

    filename = archive_url.split('/')[-1]
    archive_path = downloads_dir / filename

    with open(archive_path, 'wb') as file:
        file.write(response.content)

    logging.info(f'Архив был загружен и сохранён: {archive_path}')


def pep(session: CachedSession) -> list[tuple[str, str | int]] | None:
    """Собрать статистику статусов документов PEP."""
    statuses_dict = {}

    response = get_response(session, PEP_PYTHON_URL)
    if response is None:
        return

    soup = BeautifulSoup(response.text, features='lxml')
    pep_list = soup.find_all('tr', class_=['row-even', 'row-odd'])

    logging.info('Начата проверка статусов PEP.')
    mismatches_count = 0

    for pep_tag in tqdm(pep_list):
        first_column_tag = pep_tag.find('abbr')
        if first_column_tag is None:
            continue

        preview_status = first_column_tag.text[1:]
        link = find_tag(pep_tag, 'a', {'class': 'internal'})

        if link.text.strip() == '0':
            logging.info('Пропущен PEP 0.')
            continue

        link_url = urljoin(PEP_PYTHON_URL, link['href'])

        response = get_response(session, link_url)
        if response is None:
            logging.warning(f'Не удалось загрузить PEP: {link_url}')
            continue

        soup = BeautifulSoup(response.text, features='lxml')
        actual_status = get_pep_status(soup, link_url)

        statuses_dict[actual_status] = statuses_dict.get(actual_status, 0) + 1

        expected_statuses = EXPECTED_STATUS[preview_status]

        if actual_status not in expected_statuses:
            mismatches_count += 1
            logging.info(
                f'{link_url}\n'
                f'Статус в карточке: {actual_status}\n'
                f'Ожидаемые статусы: {list(expected_statuses)}'
            )

    results = [('Статус', 'Количество')]
    results.extend(statuses_dict.items())
    total = sum(statuses_dict.values())
    results.append(('Total', total))

    logging.info(
        f'Проверка статусов PEP завершена. '
        f'Обработано: {total}. '
        f'Несовпадений: {mismatches_count}.'
    )

    return results


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
    'pep': pep,
}


def main() -> None:
    """Обрабатывает аргументы командной строки и запускает парсер."""
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

    logging.info('Парсер завершил работу.')


if __name__ == '__main__':
    main()
