import asyncio
import os
import platform
import sys
from datetime import datetime, timedelta

import aiohttp


def change_base_currency(currency=None):
    if currency:
        base_currency = currency
    else:
        base_currency = ("USD", "EUR")
    return base_currency


async def fetch_currency_rate(data, base_currency, date_str):
    curr_dict_res = data.get('exchangeRate')
    fdata = {}
    date_currency_dict = {}
    norm_resp = ""
    for curr_dict in curr_dict_res:
        currency = curr_dict.get('currency')
        base_ccy = str(curr_dict.get('baseCurrency'))
        if currency in base_currency:
            sale = curr_dict.get('saleRate', curr_dict.get('saleRateNB'))  # використовується saleRateNB як запасний
            purchase = curr_dict.get('purchaseRate', curr_dict.get('purchaseRateNB'))  # аналогічно
            # Перевіряємо, чи існують sale та purchase, інакше пропускаємо цю валюту
            if sale and purchase:
                date_currency_dict[currency] = {'sale': sale, 'purchase': purchase}
                norm_resp += (f"{date_str} Валюту {currency} можна купити за {sale} {base_ccy},"
                              f" а продати - за {purchase} {base_ccy}\n")
    if date_currency_dict:  # Переконуємося, що додавання відбувається, якщо є дані
        fdata = {date_str: date_currency_dict}
    print(norm_resp)
    return fdata, norm_resp


async def pb_ex(days_from, currency, ret):
    final_list_dict = []
    final_string = ""
    async with aiohttp.ClientSession() as session:
        for day_offset in range(days_from):
            date = datetime.now() - timedelta(days=day_offset)
            date_str = date.strftime('%d.%m.%Y')
            url = f"https://api.privatbank.ua/p24api/exchange_rates?json&date={date_str}"
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        # html = await response.text()
                        # print(url, html[:150])
                        # print("Status:", response.status)
                        # print("Content-type:", response.headers['content-type'])
                        # print('Cookies: ', response.cookies)
                        # print(response.ok)
                        data = await response.json()
                        d = data.get("exchangeRate")
                        if d:
                            fdata, norm_resp = await fetch_currency_rate(data, currency, date_str)
                            final_list_dict.append(fdata)
                            final_string += f"{norm_resp}\n"
                        else:
                            final_list_dict.append(f"За {date_str} даних по курсу обміну немає")

                    else:
                        print(f"Error status: {response.status} for {url}")
            except aiohttp.ClientConnectorError as err:
                print(f'Connection error: {url}', str(err))
            except Exception as err:
                print(f"Error fetching data for {date}: {err}")
                return None
        # print(final_list_dict)
        if ret == 1:
            return final_list_dict
        else:
            return final_string


if __name__ == "__main__":
    try:
        curr = change_base_currency(sys.argv[2])
    except IndexError:
        curr = change_base_currency()
    if len(sys.argv) < 2:
        current_file_path = os.path.abspath(__file__)
        days_from_now = int(input(f"Usage: python {current_file_path} <number_of_days> <choose_another_currency>"))
        if platform.system() == 'Windows':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        print(asyncio.run(pb_ex(days_from_now, curr, 1)))
    else:

        days_from_now = int(sys.argv[1])
        if days_from_now > 10:
            print("Error: Number of days must not exceed 10.")
        else:
            if platform.system() == 'Windows':
                asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            print(asyncio.run(pb_ex(days_from_now, curr, 1)))
