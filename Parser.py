from lib2to3.pgen2.parse import ParseError
from tkinter import UNDERLINE
from xml.etree.ElementTree import TreeBuilder
import requests
from bs4 import BeautifulSoup
import time
import sqlite3
from termcolor import colored, cprint

class DBManager:

    def __init__(self, con, cur):
        self.con = con
        self.cur = cur
        DBManager.CreateDataBase(self)

    def CreateDataBase(self):

        self.cur.execute("""CREATE TABLE IF NOT EXISTS data (ID bigint, 
                                                       LotName text,
                                                       LotPrice text,
                                                       LotPriceInt bigint,
                                                       LotURL text)""")

        self.con.commit()

    def InsertInDB(self, LotID, name, price, priceint, url_card):
        self.cur.execute(f'INSERT INTO data VALUES (?, ?, ?, ?, ?)', (LotID, name, price, priceint, url_card))
        self.con.commit()

    def DataCheck(self, url):
        self.cur.execute(f'SELECT LotURL FROM data WHERE LotURL = "{url}"')
        return self.cur.fetchone()


class AvitoParser(DBManager):

    """Program class for parsing the avito.ru web service on the page: https://www.avito.ru/moskva/tovary_dlya_kompyutera/komplektuyuschie/videokarty-ASgBAgICAkTGB~pm7gmmZw?cd=1"""

    headers = {
        "accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36"
    }

    def Parse(self):

        page = 1
        LotID = 1

        while True:
            try:
                num = 1
                url = f'https://www.avito.ru/moskva/tovary_dlya_kompyutera/komplektuyuschie/videokarty-ASgBAgICAkTGB~pm7gmmZw?cd=1&p={page}'
                print(f'\n=============== P A G E: {page} ===============\n')
                time.sleep(3)
                src = requests.get(url, headers=self.headers)
                print(AvitoParser.CodeStatusCheck(code=src.status_code))
                soup = BeautifulSoup(src.text, 'lxml')
                answer = soup.find_all('div', class_ = 'iva-item-content-rejJg')
                for j in answer:
                    j = str(j)
                    soup2 = BeautifulSoup(j, 'lxml')
                    name = soup2.find('h3').text
                    price = soup2.find('span', class_ = 'price-text-_YGDY text-text-LurtD text-size-s-BxGpL').text
                    url_card = 'https://avito.ru'+AvitoParser.ParseTeg(str(soup2.find('a')), 'href')
                    answer = AvitoParser.ParseFromDB(DBManager.DataCheck(self, url_card))
                    if answer[0] != None:
                        pass
                    else:
                        DBManager.InsertInDB(self, LotID, name, price, AvitoParser.ParsePrice(price), url_card)
                        if answer[1] == 'New!':
                            print(f"{colored(num, 'green')} --> Lot name: {name} | Lot price: {price} | {url_card} | Lot status: {colored(answer[1], 'green', attrs=['underline'])}")
                        else:
                            print(f"{colored(num, 'magenta')} --> Lot name: {name} | Lot price: {price} | {url_card} | Lot status: {colored(answer[1], 'magenta')}")
                    num += 1
                    LotID += 1

                page += 1

            except KeyboardInterrupt:
                print('Program stoped')
                exit(1)

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
