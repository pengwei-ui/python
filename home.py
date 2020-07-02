import requests
import re
import time
import json
from lxml import etree
from fake_useragent import UserAgent
from PIL import Image
import pytesseract
import pymysql
import pprint


class ZiruHome(object):
    def __init__(self):
        self.headers = {
            'Host': 'www.ziroom.com',
            'user-agent': UserAgent().random
        }
        self.real_num = {}
        pass

    def get_html(self,url):
        resp = requests.get(url=url, headers=self.headers, timeout=10)
        code = resp.status_code
        self.content = resp.text
        imgurl = re.findall(r'<span class="num" style="background-image: url(.*?);background-position:.*?"></span>',
                            resp.text)[0].replace('(', '').replace(')', '')
        image_url = 'http:'+imgurl
        if code == 200:
            with open('data.html', 'w', encoding='utf-8')as f:
                f.write(resp.text)
                f.close()
            return image_url
        else:
            print('获取失败！！', code)
        pass

    def download_img(self, image_url):
        resp = requests.get(url=image_url)
        file_name = image_url.split('/')[-1]
        with open(file_name, 'wb') as f:
            f.write(resp.content)
            f.close()
            pass
        return file_name

    def parse_img(self, file_name):
        image = Image.open(file_name)
        nums = pytesseract.image_to_string(image)
        nums = [num for num in nums]
        for num in nums:
            if num == ' ':
                nums.remove(num)
        self.offset = ['-0px', '-21.4px', '-42.8px', '-64.2px', '-85.6px',
                       '-107px', '-128.4px', '-149.8px', '-171.2px', '-192.6px']
        for k, v in zip(self.offset, nums):
            self.real_num[k] = v
        # print(self.real_num)

    def get_data(self):
        contents = etree.HTML(self.content)
        real_price = []
        name = contents.xpath('.//div[2]/h5/a/text()')
        floor_size = contents.xpath(
            '/html/body/section/div[3]/div[2]/div/div[2]/div[1]/div[1]/text()')
        location = contents.xpath(
            '//section/div[3]/div[2]/div/div[2]/div/div[2]/text()')
        home_offset = re.findall(
            r'<span class="rmb">￥</span>(.*?)</div>', self.content, re.S)
        for offsets in home_offset:
            offsets = re.findall(
                'background-position: (.*?)"></span>', offsets)
            price = ''
            for offset in offsets:
                price += self.real_num[offset]
            real_price.append(price)
            price = ''
        data = {}
        try:
            for name, price, floor_size, location in zip(name, real_price, floor_size, location):
                infos = name.split('·')
                items = floor_size.split('|')
                size=re.findall(r'(.*?)㎡',str(items[0]))[0]
                data['style'] = str(infos[0])
                data['name'] = str(infos[1])
                data['floor'] = str(items[1])
                data['size'] = float(size)
                data['price'] = float(price)
                data['location'] = location.replace(
                    '\n', '').replace('\t', '').strip()
                self.save(data)
        except:
            print('数据错误')
        pass

    def save(self, data):
        db = pymysql.connect(host='localhost', port=3306,
                             db='pengwei', user='pengwei', password='pengwei')
        cursor = db.cursor()
        cursor.execute(
            """ INSERT into ziru value(%s, %s, %s, %s, %s, %s)"""
            ,(data['name'], data['style'], data['size'], data['price'], data['floor'], data['location'])
        )
        db.commit()
        cursor.close()
        pass
    pass

if __name__ == "__main__":
    for i in range(1,51):
        url = f'http://www.ziroom.com/z/p{i}/'
        home = ZiruHome()
        image_path = home.get_html(url)
        image = home.download_img(image_path)
        home.parse_img(image)
        home.get_data()
        print('正在爬取第{}'.format(i))
        pass
    pass