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
MM_ADRS = os.environ.get('MM_ADRS')
MM_PK = os.environ.get('MM_PK')


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

    #print()
    #print(f"Fetching 1Inch aggregated quote for {token_out_symbol}...")


    amount_in = int(amount_in * token_in_decimals)

    oneinch_url = f'https://api.1inch.dev/swap/v5.2/137/quote?src={token_in}&dst={token_out}&amount={amount_in}'

    quote = requests.get(oneinch_url, headers=headers).json()
                
    if 'toAmount' in quote:
        amount_out = int(quote['toAmount'])
        #print()
        ##print(f'Swap {amount_in / token_in_decimals} {token_in_symbol} for: {amount_out / token_out_decimals} {token_out_symbol}')
        #print()
        amount_out = amount_out / token_out_decimals
        return amount_out
    else:
        print(quote['description'])
        amount_out = 0
        return amount_out

#get_quote('0xc2132d05d31c914a87c6611c10748aeb04b58e8f', '0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359', 1)

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

    allowance = token_in_contract.functions.allowance(w3.to_checksum_address(address), one_inch_address).call()
    print(f'Allowance to the Router through Contract: {str(allowance)} {token_in_symbol}')
    
    
    oneinch_url = f'https://api.1inch.dev/swap/v5.2/137/approve/allowance?tokenAddress={token_in}&walletAddress={address}'
    allowance = requests.get(oneinch_url, headers=headers).json()['allowance']
    print(f'Allowance to the Router through API: {str(allowance)} {token_in_symbol}')
    

    
    if int(allowance) <= 0:

        nonce = w3.eth.get_transaction_count(address)

        txn = token_in_contract.functions.approve(one_inch_address, amount_in).build_transaction({
            'from': address,
            'nonce': nonce
            })
        signed = w3.eth.account.sign_transaction(txn, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
        tx = w3.eth.get_transaction(tx_hash)
    
    


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

    
    slippage = 0.01 # x%

    oneinch_url = f'https://api.1inch.dev/swap/v5.2/137/swap?src={token_in}&dst={token_out}&amount={amount_in}&from={address}&slippage={slippage}'

    swap_data = requests.get(oneinch_url, headers=headers).json()

    print(swap_data)



def get_swap_callback(src, dst, amount, from_smartcontract):
    try:
        slippage = 0 #1%
        apiUrl = f"https://api.1inch.dev/swap/v5.2/137/swap?src={src}&dst={dst}&amount={amount}&from={from_smartcontract}&slippage={slippage}&disableEstimate=true"
        response = requests.get(apiUrl, headers=headers).json()
        if response['tx']['data']:
            to_amt = response['toAmount']
            callback_data = response['tx']['data']
            return to_amt, callback_data
        else:
            print(str(response))
    except:
        print()
        print("1inch API err, response above...")

'''
get_swap_callback(Web3.to_checksum_address('0x7ceb23fd6bc0add59e62ac25578270cff1b9f619'), 
             Web3.to_checksum_address('0xc2132d05d31c914a87c6611c10748aeb04b58e8f'), 
             100000000000000000000000000, 
             MM_ADRS, )
'''
#https://ethereum.stackexchange.com/questions/129138/can-i-use-the-data-returned-from-1inchs-api-swap-to-perform-a-swap-from-a-smar