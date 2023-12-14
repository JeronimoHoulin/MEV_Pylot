import os
from dotenv import load_dotenv
from web3 import Web3
import json
import time

from web3.middleware import geth_poa_middleware
from one_inch import get_swap_callback

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

############# DEPLOYED CONTRACTS !!!!!!!!!!!
flash_swap_adrs = Web3.to_checksum_address(os.environ.get('FLASH_SWAP_ADDRSS')) 
dodo_flash_adrs = Web3.to_checksum_address(os.environ.get('DEPLOYED_DODO_SWAP')) 
DEPLOYED_DODO_SWAP = os.environ.get('DEPLOYED_DODO_SWAP')




def approve_flashswap(token_in_contract):
    #APPROVE THE FLASH LOAN ABI contract (ADD IF NO APPROVAL)
    nonce = w3.eth.get_transaction_count(mm_address)

    txn = token_in_contract.functions.approve(flash_swap_adrs, int(100*1e18)).build_transaction({
        'from':mm_address,
        'nonce': int(nonce)
        })
    signed = w3.eth.account.sign_transaction(txn, mm_pk)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    tx = w3.eth.get_transaction(tx_hash)
    return tx.hex()


def flash_swap(token_in, symb, token_through, fee0, fee1, amount_in):

    uni_factory_adrs = Web3.to_checksum_address('0x1F98431c8aD98523631AE4a59f267346ea31F984')

    with open('abi/uni_factory.json') as f:
        uni_factory_abi = json.load(f)
    uni_factory_contract  = w3.eth.contract(uni_factory_adrs, abi=uni_factory_abi)

    token_in = Web3.to_checksum_address(token_in)
    token_through = Web3.to_checksum_address(token_through)
    amount_in = int(amount_in)
    fee0 = int(fee0)
    fee1 = int(fee1)

    pool0 = uni_factory_contract.functions.getPool(
        token_in,
        token_through,
        fee0
    ).call()

    pool0 = Web3.to_checksum_address(pool0)

    #params TO BE FOUD AUTOMATED:
    pool0, fee1, token_in, token_through, amount_in = pool0, fee1, token_in, token_through, amount_in
    #print(f"Params: {pool0, fee1, token_in, token_through, amount_in}")


    #Build ERC20 contract
    with open('abi/ERC20.json') as f:
        erc_abi =  json.load(f)
    token_in_contract = w3.eth.contract(address=token_in, abi=erc_abi)


    #connect the FLACHLOAN CONTRACT & ABI
    with open('contracts/flash_loan_abi.json') as f:
        flash_loan_abi = json.load(f)

    flash_swap_contract = w3.eth.contract(flash_swap_adrs, abi=flash_loan_abi)


    allowance_granted = token_in_contract.functions.allowance(mm_address, flash_swap_adrs).call()
    #print("Allowance granted to Flash Loan Contract: " + str(allowance_granted/1e18) + ' {symb}.')
    #print()

    
    if allowance_granted <= 0:
        tx = approve_flashswap(token_in_contract)      
        if tx:
            pass
        else:
            time.sleep(15)



    #Check WETH Balance before flash loan:
    token_in_decimals = token_in_contract.functions.decimals().call()
    #init_balance = token_in_contract.functions.balanceOf(mm_address).call() / token_in_decimals
    print()
    print(f'Initiating Flash Swap with {amount_in/(10 ** token_in_decimals)} {symb}')
    print()

    nonce = w3.eth.get_transaction_count(mm_address)

    #send flash loan with more than balance (balance is to pay fee...)
    swap = flash_swap_contract.functions.flashSwap(
        pool0, 
        fee1, 
        token_in, 
        token_through, 
        amount_in
        ).build_transaction({
            'chainId': 137,
            'gas': int(5000000),
            'nonce': nonce,
            'from': mm_address
        })
                
    signed = w3.eth.account.sign_transaction(swap, mm_pk)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    print('----')
    print(f' Tx Hash: {tx_hash.hex()}')
    print('----')

    print()
    print()



def dodo_loan_swap(flashLoanPool, loanToken, throughToken, loanAmount, minOutOneInch, unifee, _dataOneInch):
    '''
        address flashLoanPool, 
        address loanToken, 
        address throughToken, 
        uint256 loanAmount, 
        uint minOutOneInch, 
        uint24 unifee,
        bytes memory _dataOneInch
    '''
    with open('contracts/dodo_loan_abi.json') as f:
        dodo_loan_abi = json.load(f)
    dodo_swap_contract = w3.eth.contract(dodo_flash_adrs, abi=dodo_loan_abi)

    nonce = w3.eth.get_transaction_count(mm_address)

    flash_arb = dodo_swap_contract.functions.dodoFlashLoan(
        flashLoanPool, 
        loanToken, 
        throughToken, 
        loanAmount, 
        minOutOneInch, 
        unifee,
        bytes.fromhex(_dataOneInch[2:]) # Remember to jump over 0x...
    ).build_transaction({
            'chainId': 137,
            'gas': int(500000),  # Increase the gas limit as needed
            'gasPrice': w3.to_wei('130', 'gwei'),  # Set an appropriate gas price from API maybe ? => requests.get('https://gasstation-testnet.polygon.technology/v2').json()
            'nonce': nonce,
            'from': mm_address
        })

    print(flash_arb)
    print(flash_arb.text())
    print(str(flash_arb))
                
    signed = w3.eth.account.sign_transaction(flash_arb, mm_pk)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    print('----')
    print(f'Flash Arbi Tx Hash: {tx_hash.hex()}')
    print('----')

    print()
    print()
    

'''
#test
amount, callback = get_swap_callback('0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359', '0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619', 100000000, DEPLOYED_DODO_SWAP)

dodo_loan_swap('0x813FddecCD0401c4Fa73B092b074802440544E52',
                '0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359', 
                '0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619', 
                100000000, 
                int(amount), 
                500,
                callback)


'''


