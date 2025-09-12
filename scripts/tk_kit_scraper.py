import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


def scrape_and_structure_for_llm(base_url, initial_file_path):
    """
    This script scrapes documentation pages, extracts key content,
    and structures it into a clean, style-free HTML file optimized for LLMs.

    Args:
        base_url (str): The base URL of the documentation website.
        initial_file_path (str): The file path to the initial HTML table of contents.
    """
    try:
        with open(initial_file_path, 'r', encoding='utf-8') as f:
            initial_content = f.read()
    except FileNotFoundError:
        print(f"Ошибка: Файл '{initial_file_path}' не найден.")
        return

    soup = BeautifulSoup(initial_content, 'html.parser')

    # --- Извлечение уникальных ссылок ---
    links = []
    nav_menu = soup.find('ul', id='api-menu')
    if nav_menu:
        for link in nav_menu.find_all('a', href=True):
            # Собираем только ссылки на страницы с документацией API
            if link['href'].startswith('/developers/api-doc/'):
                full_url = urljoin(base_url, link['href'])
                if full_url not in links:
                    links.append(full_url)

    if not links:
        print("Не найдено ссылок для обхода.")
        return

    # --- Сбор и очистка контента ---
    all_content = ""
    for url in links:
        try:
            print(f"Обрабатывается: {url}")
            response = requests.get(url)
            response.raise_for_status()

            page_soup = BeautifulSoup(response.text, 'html.parser')
            content_div = page_soup.find(id='right-bar')

            if content_div:
                # Удаляем все атрибуты стиля, классы и т.д. для чистоты
                for tag in content_div.find_all(True):
                    tag.attrs = {}

                # Добавляем разделитель перед контентом новой страницы
                all_content += f"\n"
                all_content += str(content_div)
                all_content += f"\n\n<hr>\n"
            else:
                print(f"Контент 'right-bar' не найден на: {url}")

        except requests.exceptions.RequestException as e:
            print(f"Не удалось получить доступ к {url}: {e}")

    # --- Создание итогового HTML без стилей ---
    final_html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Сводная документация API для LLM</title>
</head>
<body>
    <h1>Сводная документация по API</h1>
    {all_content}
</body>
</html>
    """

    output_filename = 'llm_optimized_documentation.html'
    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(final_html)
        print(f"\nДокументация успешно сохранена в файл '{output_filename}'")
    except IOError as e:
        print(f"Ошибка при записи в файл '{output_filename}': {e}")


# --- Запуск ---
if __name__ == '__main__':
    BASE_URL = 'https://tk-kit.ru'
    # Убедитесь, что файл QA.html находится в той же директории, что и скрипт
    INITIAL_FILE = 'QA.html'
    scrape_and_structure_for_llm(BASE_URL, INITIAL_FILE)