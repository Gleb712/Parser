import requests
from bs4 import BeautifulSoup as bs
from models import Item
from sqlalchemy.orm import Session


# Получение количества страниц в категории
def get_page_count():
    url = f"https://www.maxidom.ru/search/catalog/?q=молоток&amount=30&PAGEN_10=1"
    response = requests.get(url)
    soup = bs(response.text, features="lxml")
    page_count = int(soup.find(class_="lvl2__content-nav-numbers-number").text.split()[-1])
    return page_count

# Запрос страницы и получение HTML
def get_response(page: int, search: str):
    url = f"https://www.maxidom.ru/search/catalog/?q={search}&amount=30&PAGEN_10={page}"
    response = requests.get(url)
    print(response.status_code)
    if response.status_code == 200:
        return bs(response.text, "html.parser")
    else:
        raise Exception(f"Ошибка при запросе: {response.status_code}")

# Получение названий и цен
def get_names_and_prices(soup: bs):
    all_names = soup.findAll(itemprop="name")[1:]
    all_prices = soup.findAll(class_="l-product__price-base")
    return all_names, all_prices

# Сохранение товаров в базу данных
def save_to_database(all_names, all_prices, session):
    for name, price in zip(all_names, all_prices):
        item_name = name.text.strip()
        item_price = int(price.text.replace(" ", "").replace("\n", "").replace("₽/шт.", ""))
        existing_item = session.query(Item).filter(Item.name == item_name, Item.price == item_price).first()
        if not existing_item:
            new_item = Item(name=item_name, price=item_price)
            session.add(new_item)
    session.commit()

# Основная функция для парсинга и сохранения
def parse_and_save(session: Session):
    search = "молоток"  # Укажите категорию поиска
    for page in range(get_page_count()):
        page += 1
        soup = get_response(page, search)
        if not soup:
            break
        all_names, all_prices = get_names_and_prices(soup)
        save_to_database(all_names, all_prices, session)
        print(f"Страница {page} обработана")
