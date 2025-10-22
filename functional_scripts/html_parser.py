# html_parser_parser.py
from bs4 import BeautifulSoup
import re


def split_title(title_full: str):
    """
    Разделяет название детали и модель автомобиля по двойному пробелу.
    Если модели нет, возвращает None.
    """
    parts = title_full.split("  ", 1)  # split по двойному пробелу, максимум 2 части
    detail_name = parts[0].strip()
    car_model = parts[1].strip() if len(parts) > 1 else None
    return detail_name, car_model

def parse_catalog_page(html: str, existing_keys=None):
    """
    Парсит страницу каталога, собирает характеристики, разделяет название и модель.
    
    :param html: HTML страницы
    :param existing_keys: set, если есть предыдущие ключи характеристик
    :return: tuple (items, all_keys)
    """
    if existing_keys is None:
        existing_keys = set()

    soup = BeautifulSoup(html, "html.parser")
    items = []

    for card in soup.select("div.main-content.new-border-grid ul > li.new-grid__item"):
        title_tag = card.select_one("div.item-title a")
        price_tag = card.select_one("div.item-price.flex-col .prices-not_checkbox span")
        link_tag = card.select_one("div.item-title a")
        sku_tag = card.select_one("div.item-article span")
        img_tag = card.select_one("div.item-image img")

        # SKU
        sku = None
        if sku_tag:
            text = sku_tag.get_text(strip=True)
            if "Артикул товара:" in text:
                sku = text.split("Артикул товара:")[-1].strip()

        # Разделение title на название детали и модель автомобиля
        # Разделение title на название детали и модель автомобиля
        title_full = title_tag.get_text(strip=True) if title_tag else None
        detail_name, car_model = (None, None)
        if title_full:
            detail_name, car_model = split_title(title_full)
        # Сбор характеристик
        characteristics = {}
        char_container = card.select_one(".item-characteristics")
        if char_container:
            for tr in char_container.select("tr"):
                th = tr.select_one("th")
                td = tr.select_one("td")
                if th and td:
                    key = th.get_text(strip=True).rstrip(":")
                    value = td.get_text(strip=True)
                    characteristics[key] = value
                    existing_keys.add(key)

        # Собираем данные карточки
        item_data = {
            "title": detail_name,
            "car_model": car_model,
            "price": price_tag.get_text(strip=True) if price_tag else None,
            "link": link_tag["href"] if link_tag else None,
            "sku": sku,
            "image": img_tag["src"] if img_tag else None
        }

        # Добавляем характеристики
        item_data.update(characteristics)

        # Добавляем отсутствующие ключи как None
        for key in existing_keys:
            item_data.setdefault(key, None)

        items.append(item_data)

    return items, existing_keys

from bs4 import BeautifulSoup

def parse_detail_page(html: str) -> dict:
    """
    Парсит таблицу характеристик в блоке <tbody>.
    Если в ячейке есть ссылки <a>, добавляет текст и URL.
    """
    soup = BeautifulSoup(html, "html.parser")
    data = {}

    tbody = soup.select_one("tbody")
    if not tbody:
        return {"extra_data": data}

    for tr in tbody.select("tr"):
        th = tr.select_one("th")
        td = tr.select_one("td")

        if not th or not td:
            continue

        key = th.get_text(strip=True).rstrip(":")

        # если в td есть ссылки
        links = td.find_all("a")
        if links:
            parts = []
            # проходим по всем ссылкам и собираем их текст + URL
            for a in links:
                text = a.get_text(strip=True)
                href = a.get("href", "").strip()
                if text and href:
                    parts.append(f"{text} ({href})")
                elif text:
                    parts.append(text)
            # добавляем оставшийся текст вне ссылок
            other_text = td.get_text(" ", strip=True)
            for l in links:
                lt = l.get_text(strip=True)
                if lt in other_text:
                    other_text = other_text.replace(lt, "").strip()
            if other_text:
                parts.append(other_text)
            value = " ".join(parts).strip()
        else:
            # просто текст
            value = td.get_text(" ", strip=True)

        data[key] = value

    return {"extra_data": data}

def get_total_pages(html: str) -> int:
    """
    Извлекает общее количество страниц каталога из HTML.
    Ищет атрибут grid-page-count или текст 'Страница: X / Y'.

    :param html: HTML-код страницы каталога
    :return: Количество страниц (int)
    """
    soup = BeautifulSoup(html, "html.parser")

    # Попытка 1 — найти по атрибуту grid-page-count
    badge_div = soup.find("div", attrs={"grid-page-count": True})
    if badge_div:
        try:
            return int(badge_div.get("grid-page-count"))
        except (ValueError, TypeError):
            pass

    # Попытка 2 — поиск текста "Страница: X / Y"
    text = soup.get_text(separator=" ", strip=True)
    match = re.search(r"Страница:\s*\d+\s*/\s*(\d+)", text)
    if match:
        return int(match.group(1))

    # Если ничего не найдено
    return 1