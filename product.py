import re
from lxml.html import document_fromstring
from copy import copy
import requests
import os

class Product:
    def __init__(self, name, link, price, sizes, id, main_link) -> None:
        self.name = self.normalize(name)
        self.link = link
        self.id = id
        self.main_link = main_link
        self.price = re.findall('\d+', price.replace(' ', ''))[0]
        self.article = ''
        self.path = ''
        self.tags = {}
        self.recomendations = []
        self.sizes = list(map(self.normalize, sizes))
        self.image_link = ''
        self.characteristic = {}

        self.char_names = {'Бренд': 'brand',
                           'Страна': 'country',
                           'Пол': 'genre',
                           'Основной материал': 'main_material',
                           'Дополнительный материал': 'other_material',
                           'Отделка': 'furnish',
                           'Цвет': 'color',
                           'Сезон': 'seasons',
                           'Подкладка': 'lining',
                           'Внутренний материал': 'inner_material'}
    
    def load_all(self, session:requests.Session):
        data = session.get(self.link)
        if data.status_code != 200:
            print('error')
            return
        try:
            doc = document_fromstring(data.text)
            container = doc.xpath('//div[@class="wr_item_2_2"]')

            self.characteristic = self.get_characteristic(container)
            self.article = self.characteristic.pop('Артикул')

            path = doc.xpath('//span[@itemprop="name"]/text()')
            if path:
                self.path = self.normalize(':'.join(path[1:]))
            
            discount = doc.cssselect('p.attr_discount')
            if discount:
                self.tags['discount'] = self.normalize(discount[0].xpath('./text()')[0])
            
            new = doc.cssselect('p.newnew')
            if new:
                self.tags['new'] = True
            
            recomends = doc.xpath('//li[@class="rec_li"]/a[@class="link"]/@href')
            if recomends:
                self.recomendations = [self.main_link + link for link in recomends]

            image_link = doc.xpath('//a[@id="zoom1"]/@href')
            if image_link:
                self.image_link = self.main_link + image_link[0]
                self.load_image(session)
            
        except Exception as msg:
            print(msg)
        
    def get_characteristic(self, container) -> dict:
        characteristic = {}
        for desc in container[0].xpath('./div'):
            text = self.normalize(desc.text_content())
            data = text.split(':')
            if len(data) == 2:
                name, value = data
            characteristic[name] = value.strip()
        return characteristic
    
    def load_image(self, session:requests.Session):
        data = session.get(self.image_link)
        if data.status_code != 200:
            print(f'Ошибка загрузки картинки - {self.article}')
            return
        
        content = data.content
        with open(f'images/{self.id}.jpeg', 'wb') as file:
            file.write(content)
        
            
    def to_dict(self):
        out = {'article': self.article,
               'link': self.link,
               'id': self.id,
               'name': self.name,
               'price': self.price,
               'sizes': self.sizes,
               'path': self.path,
               'recomendations': self.recomendations}
        if self.tags:
            out['tag'] = self.tags
        characteristic = copy(self.characteristic)
        for char in self.char_names:
            if char in self.characteristic:
                out[self.char_names[char]] = characteristic.pop(char)
        if len(characteristic) > 0:
            out['other_characteristics'] = characteristic
        return out

    def normalize(self, value):
        return value.strip().replace('\n', '')
    
    def __repr__(self) -> str:
        return self.article