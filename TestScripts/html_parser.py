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