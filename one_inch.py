import os
from dotenv import load_dotenv
from web3 import Web3
from web3.middleware import geth_poa_middleware
import json
import requests


#Connecting to ENV file
os.chdir('C:/Users/jeron/OneDrive/Desktop/Projects/Web3py') #Your CWD
load_dotenv()

HTTPS_PROVIDER = os.environ.get('HTTPS_PROVIDER')
ONEINCH_API_KEY = os.environ.get('ONEINCH_API_KEY')

headers = {
    "accept": "application/json",
    "Authorization": f"Bearer {ONEINCH_API_KEY}"
}



#Creating Web3 instance
w3 = Web3(Web3.HTTPProvider(HTTPS_PROVIDER))

#inject middleware for POA chain Polygon
w3.middleware_onion.inject(geth_poa_middleware, layer=0)


def get_quote(token_in, token_out, amount_in):

    token_in = w3.to_checksum_address(token_in)
    token_out = w3.to_checksum_address(token_out)


    with open('abi/ERC20.json') as f:
        ERC_20_ABI = json.load(f)

    token_in_contract =  w3.eth.contract(address=token_in, abi=ERC_20_ABI)
    token_out_contract = w3.eth.contract(address=token_out, abi=ERC_20_ABI)
    token_in_decimals = 10 ** token_in_contract.functions.decimals().call()
    token_out_decimals = 10 ** token_out_contract.functions.decimals().call()
    token_in_symbol = token_in_contract.functions.symbol().call()
    token_out_symbol = token_out_contract.functions.symbol().call()

    amount_in = amount_in * token_in_decimals

    oneinch_url = f'https://api.1inch.dev/swap/v5.2/137/quote?src={token_in}&dst={token_out}&amount={amount_in}'

    quote = requests.get(oneinch_url, headers=headers).json()
                
    if 'toAmount' in quote:
        amount_out = int(quote['toAmount'])
        print(f'You can sell {amount_in / token_in_decimals} {token_in_symbol} for: {amount_out / token_out_decimals} {token_out_symbol}')
    else:
        print(quote['description'])

def approve_allowance(token_in, token_out, amount_in, address, private_key):
    
    token_in = w3.to_checksum_address(token_in)
    token_out = w3.to_checksum_address(token_out)


    with open('abi/ERC20.json') as f:
        ERC_20_ABI = json.load(f)

    token_in_contract =  w3.eth.contract(address=token_in, abi=ERC_20_ABI)
    token_out_contract = w3.eth.contract(address=token_out, abi=ERC_20_ABI)
    token_in_decimals = 10 ** token_in_contract.functions.decimals().call()
    token_out_decimals = 10 ** token_out_contract.functions.decimals().call()
    token_in_symbol = token_in_contract.functions.symbol().call()
    token_out_symbol = token_out_contract.functions.symbol().call()

    amount_in = amount_in * token_in_decimals


    one_inch_address = w3.to_checksum_address('0x1111111254eeb25477b68fb85ed929f73a960582')
    address = w3.to_checksum_address(address)

    #Approve

    """
    msg.sender should have already given the router an allowance of at least amountIn on the input token.
    """

    allowance_granted = token_in_contract.functions.allowance(w3.to_checksum_address(address), one_inch_address).call()
    print(f'Allowance to the Router through API: {str(allowance_granted)} {token_in_symbol}')
    
    """
    oneinch_url = f'https://api.1inch.dev/swap/v5.2/137/approve/allowance?tokenAddress={token_in}&walletAddress={address}'
    allowance = requests.get(oneinch_url, headers=headers).json()['allowance']
    print(f'Allowance to the Router through API: {str(allowance)} {token_in_symbol}')
    """

    '''
    if allowance_granted <= 0:

        nonce = w3.eth.get_transaction_count(address)

        txn = token_in_contract.functions.approve(one_inch_address, amount_in).build_transaction({
            'from': address,
            'nonce': nonce
            })
        signed = w3.eth.account.sign_transaction(txn, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
        tx = w3.eth.get_transaction(tx_hash)
    '''
    


def execute_swap(token_in, token_out, amount_in, address, private_key):
    
    token_in = w3.to_checksum_address(token_in)
    token_out = w3.to_checksum_address(token_out)

    with open('abi/ERC20.json') as f:
        ERC_20_ABI = json.load(f)

    token_in_contract =  w3.eth.contract(address=token_in, abi=ERC_20_ABI)
    token_out_contract = w3.eth.contract(address=token_out, abi=ERC_20_ABI)
    token_in_decimals = 10 ** token_in_contract.functions.decimals().call()
    token_out_decimals = 10 ** token_out_contract.functions.decimals().call()
    token_in_symbol = token_in_contract.functions.symbol().call()
    token_out_symbol = token_out_contract.functions.symbol().call()

    amount_in = amount_in * token_in_decimals

    
    slippage = 1 # x%

    oneinch_url = f'https://api.1inch.dev/swap/v5.2/137/swap?src={token_in}&dst={token_out}&amount={amount_in}&from={address}&slippage={slippage}'

    swap_data = requests.get(oneinch_url, headers=headers).json()

    print(swap_data)





#get_quote(token_in, token_out, amount_in)
#approve_allowance('0xc4558c1f12d4797db4d6919C9902D197f42e9127', 'pk', amount_in)
#execute_swap(token_in, token_out, amount_in, '0xc4558c1f12d4797db4d6919C9902D197f42e9127', 'pk')

def main(token_in, token_out, amount_in):
    get_quote(token_in, token_out, amount_in)