price = '649₽/шт.'
item_price = int(price.replace(" ", "").replace("\n", "").replace("₽/шт.", ""))
print(item_price)