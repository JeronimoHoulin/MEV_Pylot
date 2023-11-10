import os
from dotenv import load_dotenv
from web3 import Web3
import json

from web3.middleware import geth_poa_middleware


#Connecting to chain
INFURA_HTTP = 'https://polygon-mainnet.infura.io/v3/7e452892f2204d6a90e814c4a03a7b1d'

w3 = Web3(Web3.HTTPProvider(INFURA_HTTP))
#inject middleware for POA chain Polygon
w3.middleware_onion.inject(geth_poa_middleware, layer=0)
print("Connected to chain: ", w3.eth.chain_id)

#Connecting to ENV file
os.chdir('C:/Users/jeron/OneDrive/Desktop/Projects/Web3py') #Your CWD
load_dotenv()

mm_address = os.environ.get('MM_ADRS')
mm_pk = os.environ.get('MM_PK')



"""  PARAMETERS  """

os.chdir('C:/Users/jeron/OneDrive/Desktop/Projects/Web3py/abi') #Your CWD because this is in TEST folder now...


WETH = Web3.to_checksum_address('0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619')
token_through = Web3.to_checksum_address('0xc2132d05d31c914a87c6611c10748aeb04b58e8f')
flash_swap_adrs = Web3.to_checksum_address('0x49d560c63ea7050bbc601052da60cd606cc08287')

#params TO BE FOUD AUTOMATED:
pool0, fee1, token_in, token_through, amount_in = Web3.to_checksum_address('0xBB98B3D2b18aeF63a3178023A920971cf5F29bE4'), 100, WETH, token_through, int(0.001 * 1e18)


#Build ERC20 contract
with open('./ERC20.json') as f:
    erc_abi =  json.load(f)
WETH_contract = w3.eth.contract(address=WETH, abi=erc_abi)


#connect the FLACHLOAN CONTRACT & ABI
with open('./flash_loan_abi.json') as f:
    flash_loan_abi = json.load(f)

flash_swap_contract = w3.eth.contract(flash_swap_adrs, abi=flash_loan_abi)


allowance_granted = WETH_contract.functions.allowance(mm_address, flash_swap_adrs).call()
print("Allowance granted to Flash Loan Contract: " + str(allowance_granted/1e18) + ' WETH.')
print()


"""
#APPROVE THE FLASH LOAN ARBI contract (ADD IF NO APPROVAL)
nonce = w3.eth.get_transaction_count(mm_address)

txn = WETH_contract.functions.approve(flash_swap_adrs, int(100*1e18)).build_transaction({
    'from':mm_address,
    'nonce': nonce
    })
signed = w3.eth.account.sign_transaction(txn, mm_pk)
tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
tx = w3.eth.get_transaction(tx_hash)
print(tx)
"""


#Check WETH Balance before flash loan:

init_balance = WETH_contract.functions.balanceOf(mm_address).call() / 1e18
print()
print(f'Initiating Flash Swap with {allowance_granted/1e18} WETH')
print('--------------------------')
print()



nonce = w3.eth.get_transaction_count(mm_address)

#send flash loan with more than balance (balance is to pay fee...)
swap= flash_swap_contract.functions.flashSwap(
    pool0, 
    fee1, 
    token_in, 
    token_through, 
    amount_in
    ).build_transaction({
        'chainId':w3.eth.chain_id,
        'gas': int(4500000),
        'nonce': nonce
    })
        
signed = w3.eth.account.sign_transaction(swap, mm_pk)
tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
print('----')
print(f' Tx Hash: {tx_hash.hex()}')
print('----')


print(f'Balance Before: {init_balance} WETH')
print()
post_balance = WETH_contract.functions.balanceOf(mm_address).call() / 1e18

print(f'Balance After: {post_balance} WETH')
print()

if (post_balance >= init_balance):
    print("WETH profit", post_balance - init_balance)
else:
    print(swap)

    


