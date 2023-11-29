import requests

headers = {
    "accept": "application/json"
}


def get_whitelist_tokens():

    all_tokens = []

    resp = requests.get('https://api-polygon-tokens.polygon.technology/tokenlists/polygon.tokenlist.json', headers=headers).json()

    tokens = resp['tokens']

    top_tokens = tokens[3:50]

    for token in top_tokens:
        #print(token['address'])
        all_tokens.append(token['address'])
    
    return all_tokens
