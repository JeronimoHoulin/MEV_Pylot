from one_inch import get_swap_callback
import json
from web3 import Web3
from web3.middleware import geth_poa_middleware
import os
from dotenv import load_dotenv

#Connecting to chain
INFURA_HTTP = os.environ.get('HTTPS_PROVIDER')

w3 = Web3(Web3.HTTPProvider(INFURA_HTTP))
#inject middleware for POA chain Polygon
w3.middleware_onion.inject(geth_poa_middleware, layer=0)


#Connecting to ENV file
os.chdir('C:/Users/jeron/OneDrive/Desktop/Projects/Web3py') #Your CWD
load_dotenv()

mm_address = Web3.to_checksum_address(os.environ.get('MM_ADRS'))
mm_pk = os.environ.get('MM_PK')


with open('abi/ERC20.json') as f:
    erc_20_abi = json.load(f)

token =  w3.eth.contract('0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619', abi=erc_20_abi)



allowance_granted = token.functions.allowance(mm_address, Web3.to_checksum_address('0x2ddf16ba6d0180e5357d5e170ef1917a01b41fc0')).call()
print(allowance_granted)


'''
nonce = nonce = w3.eth.get_transaction_count(mm_address)

txn = token.functions.approve(Web3.to_checksum_address('0x2ddf16ba6d0180e5357d5e170ef1917a01b41fc0'), int(0*1e18)).build_transaction({
    'from':mm_address,
    'nonce': int(nonce)
    })
signed = w3.eth.account.sign_transaction(txn, mm_pk)
tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
tx = w3.eth.get_transaction(tx_hash)

print(tx_hash.hex())
'''


'''

in_token_amt, call_data = get_swap_callback('0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619',
                                             '0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270', 
                                             int(0.00174*10**18), 
                                             '0x2cC52868762ba52ed4b4b7EeDC63f6269945cE3D')
in_token_amt = int(in_token_amt)
print()
print(call_data)
print(0.00174*10**18)
print(in_token_amt)
'''

