from lib2to3.pgen2.parse import ParseError
from tkinter import UNDERLINE
from xml.etree.ElementTree import TreeBuilder
import requests
from bs4 import BeautifulSoup
import sqlite3
from termcolor import colored
import time

class DBManager:

    def __init__(self, con, cur):
        self.con = con
        self.cur = cur

    def CreateTable(self, region):

        self.cur.execute(f"""CREATE TABLE IF NOT EXISTS {region} (LotName text,
                                                                  LotPrice text,
                                                                  LotPriceInt bigint,
                                                                  LotURL text)""")

        self.con.commit()

    def InsertInDB(self, region, name, price, priceint, url_card):
        self.cur.execute(f'INSERT INTO {region} VALUES (?, ?, ?, ?)', (name, price, priceint, url_card))
        self.con.commit()
    
    def Insert(self, region, name, price, priceint, url_card):
        DBManager.InsertInDB(self, region, name, price, priceint, url_card)

    def DataCheck(self, region, url):
        try:
            self.cur.execute(f'SELECT LotURL FROM {region} WHERE LotURL = "{url}"')
            return self.cur.fetchone()
        except sqlite3.OperationalError:
            DBManager.CreateTable(self, region)
            return None


class AvitoParser(DBManager):

    """Program class for parsing the avito.ru web service on the page: https://www.avito.ru/moskva/tovary_dlya_kompyutera/komplektuyuschie/videokarty-ASgBAgICAkTGB~pm7gmmZw?cd=1"""

    headers = {
        "accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36"
    }

    def Parse(self):

        #REGIONS = ['moskva_i_mo', 'kemerovskaya_oblast', 'leningradskaya_oblas', 'novosibirskaya_oblast', 'tyumenskaya_oblast', 'irkutskaya_oblast']

        page = 1

        """url = f'https://www.avito.ru/rossiya/tovary_dlya_kompyutera/komplektuyuschie/videokarty-ASgBAgICAkTGB~pm7gmmZw?cd=1&p={page}'
        time.sleep(5)
        src = requests.get(url, headers=self.headers)
        print(AvitoParser.CodeStatusCheck(code=src.status_code))
        soup = BeautifulSoup(src.text, 'lxml')
        print(soup.find('span', class_ = 'geo-address-fhHd0 text-text-LurtD text-size-s-BxGpL').text)"""



        while True:
            try:
                num = 1
                url = f'https://www.avito.ru/rossiya/tovary_dlya_kompyutera/komplektuyuschie/videokarty-ASgBAgICAkTGB~pm7gmmZw?cd=1&p={page}'
                print(f'\n=============== P A G E: {page} ===============\n')
                time.sleep(4)
                src = requests.get(url, headers=self.headers)
                print(AvitoParser.CodeStatusCheck(code=src.status_code))
                soup = BeautifulSoup(src.text, 'lxml')
                answer = soup.find_all('div', class_ = 'iva-item-content-rejJg')
                for j in answer:
                    j = str(j)
                    lot_soup = BeautifulSoup(j, 'lxml')
                    name = lot_soup.find('h3').text
                    price = lot_soup.find('span', class_ = 'price-text-_YGDY text-text-LurtD text-size-s-BxGpL').text
                    url_card = 'https://avito.ru'+AvitoParser.ParseTeg(str(lot_soup.find('a')), 'href')
                    answer = AvitoParser.ParseFromDB(DBManager.DataCheck(self, AvitoParser.ParseRegion(url_card), url_card))
                    if answer[0] != None:
                        print(f"{colored(num, 'magenta')} --> Lot name: {name} | Lot price: {price} | {url_card} | Lot status: {colored(answer[1], 'magenta')}")
                    else:
                        DBManager.Insert(self, AvitoParser.ParseRegion(url_card), name, price, AvitoParser.ParsePrice(price), url_card)
                        print(f"{colored(num, 'green')} --> Lot name: {name} | Lot price: {price} | {url_card} | Lot status: {colored(answer[1], 'green', attrs=['underline'])}")
                    num += 1

                page += 1

            except KeyboardInterrupt:
                print('Program stoped')
                exit(1)
            
            except requests.exceptions.ChunkedEncodingError:
                pass

    def CodeStatusCheck(code):
        if code == 200:
                return colored('Ready for parsing!', 'cyan')
        elif code == 302:
            return colored('No more pages (CTRL + C for stop)', 'red')
        elif code == 404:
                return colored('Page not found (CTRL + C for stop)', 'red')
        elif code == 429:
                return colored('Sending ban (CTRL + C for stop)', 'red')
        elif code == 500:
            return colored('The server cannot process the request (CTRL + C for stop)', 'red')
        else:
            return colored(f'Code not recognized: {code} (CTRL + C for stop)', 'red')
    
    def ParseRegion(url):
        text = ''
        answer = ''
        for i in list(url):
            if text == 'https://avito.ru/':
                if i == '/':
                    return answer  
                    break
                else:
                    if i == '-':
                        answer += '_'    
                    else:
                        answer += i
            else:
                text += i
    
    def ParsePrice(text):
        answer = ''
        if text == 'Цена не указана' or text == 'Бесплатно':
            return 0
        for i in list(text):
            try:
                int(i)
            except ValueError:
                continue
            else:
                answer += i
        return int(answer)

    def ParseFromDB(text):
        if text is None:
            return [None, 'New!']
        else:
            for i in text:
                return [i, 'Lot is in the database']
    
    def ParseTeg(src, teg):
        word = ''
        answer = ''
        count = 0
        for i in list(src):
            if word == teg:
                if count == 3:
                    return answer
                    break
                if i == '"' or i == '=':
                    count += 1
                    continue
                answer += i
            elif i == ' ':
                word = ''
                continue
            else:
                word += i
        print(f'{teg} is not find :(')

def main():
    global con, cursor
    con = sqlite3.connect('AvitoDataBase.db')
    cur = con.cursor()
    parser = AvitoParser(con, cur)
    parser.Parse()
    con.close()

if __name__ == '__main__':
    main()
