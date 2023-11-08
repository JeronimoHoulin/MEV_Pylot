import requests



headers = {
    "accept": "application/json"
    }



tokens = requests.get('https://www.coingecko.com/en/categories/polygon-ecosystem', headers=headers).text

print(tokens)