import json

data = json.loads(open('main.json', 'r').read())
products = list(filter(lambda x: 'other_characteristics' in x, data))
for product in products:
    print(product['other_characteristics'])