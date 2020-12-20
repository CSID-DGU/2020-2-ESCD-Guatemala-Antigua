import requests
from bs4 import BeautifulSoup
import logging
import pandas as pd
import mysql.connector
import re

config = {
    "user": "root",
    "password": "1234",
    "host": "localhost",
    "database": "agentu", #Database name
    "port": "3306" #port는 최초 설치 시 입력한 값(기본값은 3306)
}

config_chi = {
    "user": "root",
    "password": "1234",
    "host": "localhost",
    "database": "agentu_chi", #Database name
    "port": "3306" #port는 최초 설치 시 입력한 값(기본값은 3306)
}

def crawl():
    url = 'https://dgucoop.dongguk.edu:44649/store/store.php?w=4&l=1'

    df = pd.DataFrame()

    soup = _fetch(url)
    df = _parse_data(soup)
    print(str(df.iloc[0]['floor3_id']), str(df.iloc[0]['food_id']), str(df.iloc[0]['food_name']),
          str(df.iloc[0]['allergy_list']))

    conn = mysql.connector.connect(**config)

    cursor = conn.cursor()

    cursor.execute("TRUNCATE TABLE floor3")
    conn.commit()
    sql = 'insert into floor3 (floor3_id, food_id, food_name, allergy_list) value (%s, %s, %s, %s)'

    food = str(df.iloc[0]['allergy_list'])
    temp = str(df.iloc[0]['floor3_id']), str(df.iloc[0]['food_id']), str(df.iloc[0]['food_name']), str(df.iloc[0]['allergy_list'])
    print(temp)
    cursor.execute(sql, temp)

    conn.commit()

    conn.close()
    
    conn_chi = mysql.connector.connect(**config_chi)
    cursor_chi = conn_chi.cursor()

    cursor_chi.execute("TRUNCATE TABLE floor3")
    sql_chi = 'insert into floor3 (floor3_id, food_id, food_name, allergy_list) value (%s, %s, %s, %s)'
    cursor_chi.execute(sql_chi, temp)
    conn_chi.commit()
    conn_chi.close()


def _fetch(url):
    try:
        if len(url) == 0:
            logging.warning('cannot fetch url because length is %s', url)
        # time.sleep(random.uniform(1, 3))
        session = requests.session()
        session.headers['user-agent'] = 'user-agent'
        session.headers['Referer'] = 'https://dgucoop.dongguk.edu:44649/store/store.php?w=4&l=1'
        session.headers['content-type'] = 'utf-8'
        response = session.get(url)
        res = response.status_code
        if res == 200:
            print('response success!')
        elif res == 404:
            print('not found page!')
        elif res == 500:
            print('block the page!')
        soup = BeautifulSoup(response.content, 'html.parser')
        session.close()
        return soup
    except Exception as e:
        import inspect
        print('Error : ', e)


def _parse_data(soup):
    date = soup.select_one('div#sdetail > table > tr > td > p > table:nth-child(1) > tr > td:nth-child(2) > span')
    menu = soup.select_one('div#sdetail > table > tr > td > p > table:nth-child(3) > tr:nth-child(2) > td:nth-child(2) > table > tr:nth-child(1) > td')

    menu_list = menu.text.replace('\r', '').replace('\n', ',')
    data = []
    count = 1
    m_list = []

    conn = mysql.connector.connect(**config)

    cursor = conn.cursor()

    cursor.execute("select * from food_allergy")

    row = cursor.fetchone()
    allergy_list = []
    while row:
        if row[1] in menu_list:
            if row[2] is not None:
                allergy_list.append(row[2])
                print(row[0], row[1], row[2])
        row = cursor.fetchone()

    conn.close()

    allergy_list = list(set(allergy_list))

    real_allergy_list = re.findall(r'\d+', str(allergy_list))
    #print(allergy_list)
    real_allergy_list = list(set(real_allergy_list))
    real_allergy_list = re.findall(r'\d+', str(real_allergy_list))

    request_url = "https://openapi.naver.com/v1/papago/n2mt"
    headers = {"X-Naver-Client-Id": "5OD0i2eJ1I2RmC90vZRa", "X-Naver-Client-Secret": "vqIdpZAJiw"}
    params = {"source": "ko", "target": "zh-CN", "text": menu_list}
    response = requests.post(request_url, headers=headers, data=params)

    result = response.json()
    print(result['message']['result']['translatedText'])

    menu_dic = {
        'floor3_id': 1,
        'food_id': '1',
        'food_name': result['message']['result']['translatedText'],
        'allergy_list': real_allergy_list
    }
    m_list.append(menu_dic)
    #print(m_list)
    df = pd.DataFrame(m_list)

    return df


if __name__ == "__main__":
    crawl()

