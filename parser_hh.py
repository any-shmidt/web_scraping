import csv
import datetime
import os.path
import sqlite3
import time

import fake_useragent
import pytz
import requests

moscow_tz = pytz.timezone('Europe/Moscow')
current_time = datetime.datetime.now(moscow_tz)
current_time = current_time.strftime('%H:%M-%d-%m-%Y')

search_vacancy = input('Enter the job title: ')

def make_request(keyword, page):
    url = 'https://api.hh.ru/vacancies'
    ua = fake_useragent.UserAgent()
    fake_ua = {'User-Agent': ua.random}
    params = {
        'text': keyword,
        'area': 1,
        'page': page,
        'per_page': 5,
    }

    response = requests.get(url, params=params, headers=fake_ua)

    if response.status_code == 200:
        data = response.json()
    else:
        print(f'Request failed with status code: {response.status_code}')
    return data


def create_table():
    with sqlite3.connect('vacancies.db') as db:
        cur = db.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS vacancy (
            ID INTEGER PRIMARY KEY,
            Vacancy_ID TEXT NOT NULL UNIQUE,
            Title TEXT,
            Company TEXT,
            URL TEXT,
            Experience TEXT,
            Salary_from INTEGER,
            Salary_to INTEGER
        );""")


"""Проверка, есть ли вакансия с таким id в базе данных"""
def check_id(id):
    with sqlite3.connect('vacancies.db') as db:
        cur = db.cursor()
        cur.execute("""SELECT Vacancy_ID FROM vacancy
                    WHERE Vacancy_ID = ?""", id)
    if cur.fetchone() is None:
        return True
    else:
        return False


def add_to_database(vacancy_data):
    with sqlite3.connect('vacancies.db') as db:
        cur = db.cursor()
        cur.execute("""INSERT OR IGNORE INTO vacancy (
            Vacancy_ID, Title, Company, URL, Experience, Salary_from, Salary_to)
            VALUES (?, ?, ?, ?, ?, ?, ?);""", vacancy_data)


def write_to_csv(data, value):
    file_exists = os.path.isfile('vacancies_file.csv')
        
    with open('vacancies_file.csv', 'a', newline='') as file:
        headers = ['Date', 'Vacancy_id', 'Title', 'Company', 'Vacancy_url',
                    'Experience', 'Salary_from', 'Salary_to']
        writer = csv.DictWriter(file, delimiter=';', fieldnames=headers)
        reader = csv.reader(file, delimiter=';')
        if not file_exists:
            writer.writeheader()
            writer.writerow(data)
        else:
            writer.writerow(data)


def get_vacancies():
    for page in range(0, 3):
        vacancy_data = ()
        try:           
            data = make_request(search_vacancy, page=page)
            vacancies = data.get('items', [])
            # print(vacancies[0])

            for vacancy in vacancies:
                vacancy_id = vacancy.get('id')
                vacancy_title = vacancy.get('name')
                vacancy_url = vacancy.get('alternate_url')
                experience = vacancy.get('experience', {}).get('name')
                try:
                    salary_from = vacancy.get('salary', {}).get('from')
                except AttributeError:
                    salary_from = ''

                try:
                    salary_to = vacancy.get('salary', {}).get('to')
                except AttributeError:
                    salary_to = ''
                company_name = vacancy.get('employer', {}).get("name")
                print(f'ID: {vacancy_id}\nTitle: {vacancy_title}\nCompany: {company_name}\nURL: {vacancy_url}')
                print(f'Зарплата от {salary_from} до {salary_to}')
                print(f'Опыт работы: {experience}\n')

                if check_id((vacancy_id, )):
                    add_to_database((vacancy_id, vacancy_title, company_name, vacancy_url,
                                    experience, salary_from, salary_to, ))

                data_for_csv = ({'Date': current_time, 'Vacancy_id': vacancy_id,
                                'Title': vacancy_title, 'Company': company_name,
                                'Vacancy_url': vacancy_url, 'Experience': experience,
                                'Salary_from': salary_from, 'Salary_to': salary_to})
                
                write_to_csv(data_for_csv, vacancy_id)

            time.sleep(2)
        except Exception as e:
            print(e)
            break
        # except:
        #     print('Все вакансии собраны')
        #     break

create_table()       
get_vacancies()