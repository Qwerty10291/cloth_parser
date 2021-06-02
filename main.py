import concurrent.futures
from typing import List
from lxml.html import document_fromstring
import requests
from product import Product
import csv
import json
import os

class Parser:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:88.0) Gecko/20100101 Firefox/88.0'})

        self.main_link = 'https://www.bebakids.ru'

        self.category_links = ['https://www.bebakids.ru/dlya-detei/odezhda-dlya-podrostkov',
                               'https://www.bebakids.ru/dlya-detei/detskaya-verkhnyaya-odezhda',
                               'https://www.bebakids.ru/dlya-detei/naryadnye-platya-detskie',
                               'https://www.bebakids.ru/dlya-detei/obuv-detskaya',
                               'https://www.bebakids.ru/dlya-detei/golovnye-ubory-detskie',
                               'https://www.bebakids.ru/dlya-detei/shkolnaya-forma-detskaya',
                               'https://www.bebakids.ru/dlya-detei/sumki-dlya-detei',
                               'https://www.bebakids.ru/dlya-detei/aksessuary-detskie',
                               'https://www.bebakids.ru/dlya-detei/igrushki-detskie']
            
    def parse(self):
        result = []
        with concurrent.futures.ProcessPoolExecutor(max_workers=3) as executor:
            for category in executor.map(self.parse_category, self.category_links):
                result += category
        return result
    
    def parse_category(self, link):
        executors = 2
        if link == self.category_links[0]:
            executors = 3
        page = 1
        out = []
        while True:
            print(f'Категория {link}, страница: {page}')
            data = self.session.get(f'{link}-page-{page}')
            if data.status_code == 404:
                break
            doc = document_fromstring(data.text)
            products = self.preload_products(doc)

            with concurrent.futures.ThreadPoolExecutor(max_workers=executors) as executor:
                executor.map(self.load_product, products)
            out += products
            page += 1
            break
        return out
    
    def load_product(self, product):
        product.load_all(self.session)
    
    def preload_products(self, document) -> List[Product]:
        products = []
        containers = document.xpath('//li[@class="cat_li"]')
        links = list(map(lambda container: container.xpath('./div[@class="cat_li_1"]/a/@href'), containers))
        names = list(map(lambda container: container.xpath('./div[@class="cat_li_1"]/a/div[2]/span/text()'), containers))
        prices = list(map(lambda container: container.xpath('./div[@class="cat_li_1"]/a/div[3]/span/text()'), containers))
        sizes = list(map(lambda container: container.xpath('./div[@class="cat_li_2"]//a/text()'), containers))
        ids = list(map(lambda container: container.xpath('./div[@class="cat_li_1"]/@data-id'), containers))
        for link, size, name, price, id in zip(links, sizes, names, prices, ids):
            product = Product(name[0], self.main_link + link[0], price[0], size, id[0], self.main_link)
            products.append(product)
        return products

json_file = open(input('Название json файла:'), 'w')

if 'images' not in os.listdir():
    os.mkdir('images')

parser = Parser()
products = parser.parse()
prod_dict = [product.to_dict() for product in products]
for i, prod in prod_dict:
    prod['inc_id'] = i

json_file.write(json.dumps(prod_dict, ensure_ascii=False))