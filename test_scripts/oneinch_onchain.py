
import os
from dotenv import load_dotenv
from web3 import Web3
from web3.middleware import geth_poa_middleware
import json
import requests


#Connecting to ENV file
os.chdir('C:/Users/jeron/OneDrive/Desktop/Projects/Web3py/test_scripts') #Your CWD
load_dotenv()

HTTPS_PROVIDER = os.environ.get('HTTPS_PROVIDER')
ONEINCH_API_KEY = os.environ.get('ONEINCH_API_KEY')
MM_ADRS = os.environ.get('MM_ADRS')
MM_PK = os.environ.get('MM_PK')

#Creating Web3 instance
w3 = Web3(Web3.HTTPProvider(HTTPS_PROVIDER))

#inject middleware for POA chain Polygon
w3.middleware_onion.inject(geth_poa_middleware, layer=0)



homemade_adrs = w3.to_checksum_address("0x7e72AD53c61E1804Cc5d0B855661FcE7fdE9DFf1") #0x7362321A348298830DAA75Bbc2eb643E779e2dB1

with open('oneinch.json') as f:
    homemade_abi = json.load(f)

homemade_contract =  w3.eth.contract(address=homemade_adrs, abi=homemade_abi)


headers = {
    "accept": "application/json",
    "Authorization": f"Bearer {ONEINCH_API_KEY}"
}



def get_swap_callback(src, dst, amount, from_adrs, to_adrs):
    try:
        slippage = 1 #1%
        apiUrl = f"https://api.1inch.dev/swap/v5.2/137/swap?src={src}&dst={dst}&amount={amount}&from={from_adrs}&to={to_adrs}&slippage={slippage}&disableEstimate=true"
        response = requests.get(apiUrl, headers=headers).json()
        if 'tx' in response.keys():
            to_amt = response['toAmount']
            callback_data = response['tx']['data']
            return to_amt, callback_data
        else:
            print("Unexpected response format:", response)

    except requests.exceptions.RequestException as err:
        print("1Inch API errr:", err)
        print()
        print(response)
        print(apiUrl)


amount, calldata = get_swap_callback("0xc2132D05D31c914a87C6611C10748AEb04B58e8F", "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619", 1000000, homemade_adrs, MM_ADRS)
print(calldata)

#approve the homemade contract to make the swap:

with open('../abi/ERC20.json') as f:
    ERC_20_ABI = json.load(f)

token_in_contract =  w3.eth.contract(address="0xc2132D05D31c914a87C6611C10748AEb04B58e8F", abi=ERC_20_ABI)

allowance = token_in_contract.functions.allowance(w3.to_checksum_address(MM_ADRS), homemade_adrs).call()
print(f'Allowance to the Homemade Contract: {str(allowance)} USDT')

'''

if int(allowance) <= 0:

    nonce = w3.eth.get_transaction_count(MM_ADRS)

    txn = token_in_contract.functions.approve(homemade_adrs, 2000000).build_transaction({
        'from': MM_ADRS,
        'nonce': nonce
        })
    signed = w3.eth.account.sign_transaction(txn, MM_PK)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    tx = w3.eth.get_transaction(tx_hash)
    allowance = token_in_contract.functions.allowance(w3.to_checksum_address(MM_ADRS), homemade_adrs).call()
    print(f'NEW INCREASED allowance to the Homemade Contract: {str(allowance)} USDT') 

else:
    nonce = w3.eth.get_transaction_count(MM_ADRS)
    response = homemade_contract.functions.swap(1000000, calldata).build_transaction({
            'chainId': 137,
            'gas': int(10000),  # Increase the gas limit as needed
            'gasPrice': w3.to_wei('90', 'gwei'),  # Set an appropriate gas price from API maybe ? => requests.get('https://gasstation-testnet.polygon.technology/v2').json()
            'nonce': nonce,
            'from': MM_ADRS
    })
    
    signed = w3.eth.account.sign_transaction(response, MM_PK)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    print('----')
    print(f'Flash Arbi Tx Hash: {tx_hash.hex()}')
    print('----')

    print()
    print()

'''