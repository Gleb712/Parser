import requests
from bs4 import BeautifulSoup as bs


def get_responce(search, page):
    url = f"https://www.maxidom.ru/search/catalog/?q={search}&amount=30&PAGEN_10={page}"
    response = requests.get(url).text
    soup = bs(response, "html.parser")
    return soup


def get_names_and_prices(soup):
    all_names = soup.findAll(itemprop="name")[1:]
    all_prices = soup.findAll(class_="l-product__price-base")
    return all_names, all_prices


def print_page(all_names, all_prices, page):
    print("- - - " * 17)
    print(f"Название{89 * " "}Цена")
    print("- - - " * 17)

    for a, b in zip(all_names, all_prices):
        name = a.text
        price = b.text.replace(" ", "").replace("\n", "")
        if len(name) < 75:
            print(f"{name}{(101 - len(name) - len(price)) * " "}{price}")
        else:
            print(f"{name[:75] + "..."}{(98 - len(name[:75]) - len(price)) * " "}{price}")

    print("- - - " * 17)
    print(f"{" " * (91 - len(str(page)))}Страница: {page}")
    print("- - - " * 17)


def main():
    search = input("Введите наименование товара: ")
    soup = get_responce(search, page = 1)
    pages_count = int(soup.find(class_="lvl2__content-nav-numbers-number").text.split()[-1])

    for page in range(1, pages_count + 1):
        soup = get_responce(search, page)
        all_names, all_prices = get_names_and_prices(soup)
        print_page(all_names, all_prices, page)


main()