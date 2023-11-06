import os
from dotenv import load_dotenv
from web3 import Web3
from web3.middleware import geth_poa_middleware
import json
import eth_abi.packed
import requests

import itertools

#Connecting to ENV file
os.chdir('C:/Users/jeron/OneDrive/Desktop/Projects/Web3py') #Your CWD
load_dotenv()

HTTPS_PROVIDER = os.environ.get('HTTPS_PROVIDER')

#Creating Web3 instance
w3 = Web3(Web3.HTTPProvider(HTTPS_PROVIDER))

#inject middleware for POA chain Polygon
w3.middleware_onion.inject(geth_poa_middleware, layer=0)



def get_pools(token_in, token_out):


    """
    #Using factory to get pools...

    all_fees = [100, 500, 3000, 10000]
    all_pools = []

    uni_factory_adrs = Web3.to_checksum_address('0x1F98431c8aD98523631AE4a59f267346ea31F984')

    with open('abi/uni_factory.json') as f:
        uni_factory_abi = json.load(f)
    uni_factory_contract  = w3.eth.contract(uni_factory_adrs, abi=uni_factory_abi)


    for fee in all_fees:
        
        pool = uni_factory_contract.functions.getPool(
            token_in,
            token_out,
            fee
        ).call()

        print(pool)
        print()

    """


    matching_pools = []

    token_in = token_in.lower()
    token_out = token_out.lower()

    all_pools = requests.get('https://cloudflare-ipfs.com/ipns/api.uniswap.org/v1/pools/v3/polygon-mainnet.json').json()



    #########KILL RELEVANCE OF TOKEN OUT.. ONLY LOOKING FOR TOKEN IN TO TOKEN IN NO MATTER WHAT POOLS AND HOPS:

    for pool in all_pools:
        if pool['token0']['id'] == token_in or pool['token1']['id'] == token_in and pool['tvlUSD'] > 1000:
            matching_pools.append(pool)  


    print(f'Found {len(matching_pools)} pools that have either Token0 and Token1.')
    print()
    #ORdering by tvl
    sorted_matching_pools = sorted(matching_pools, key=lambda d: d['tvlUSD'], reverse=True) 


    return sorted_matching_pools


def get_best_quote (token_in, token_out, amount_in):
    

    quote_addr = Web3.to_checksum_address('0x61fFE014bA17989E743c5F6cB21bF9697530B21e')
    with open('abi/uni_quoter_v2.json') as f:
        uni_quoter_abi = json.load(f)

    quote_contract = w3.eth.contract(quote_addr, abi=uni_quoter_abi)

    with open('abi/ERC20.json') as f:
        erc_20_abi = json.load(f)
    
    token_in = Web3.to_checksum_address(token_in)
    token_out = Web3.to_checksum_address(token_out)

    token_in_contract = w3.eth.contract(address= token_in, abi=erc_20_abi)
    token_out_contract = w3.eth.contract(address= token_out, abi=erc_20_abi)

    token_in_decimals = 10 ** token_in_contract.functions.decimals().call()
    token_out_decimals = 10 ** token_out_contract.functions.decimals().call()

    token_in_symbol = token_in_contract.functions.symbol().call()
    token_out_symbol = token_out_contract.functions.symbol().call()

    amount_in = int( amount_in * token_in_decimals)


    quote_contract = w3.eth.contract(quote_addr, abi=uni_quoter_abi)


    #for index in range(0, len(sorted_matching_pools)):

    """

    pool_id_1 = sorted_matching_pools[0]['id']
    pool_fee_1 = int(sorted_matching_pools[0]['feeTier'])

    pool_id_2 = sorted_matching_pools[1]['id']
    pool_fee_2 = int(sorted_matching_pools[1]['feeTier'])
    """

    all_fees = [100, 500, 3000, 10000]

    for fee in all_fees:
        
        #QUOTE  PATH
        # Token_In  ->    X    ->    Y    -> Token_In
        path = eth_abi.packed.encode_packed(['address','uint24','address'], [token_in, fee, token_out])
        
        amount_out, sqrtPriceX96After, initializedTicksCrossed, gasEstimate  = quote_contract.functions.quoteExactInput(
            path,
            amount_in
        ).call()

        print(f'{amount_in / token_in_decimals } {token_in_symbol}  --->   {amount_out / token_out_decimals} {token_out_symbol}.')
        print("---")

        print()









####################################### TEST....


def get_possible_cycle(sorted_matching_pools, token_in, token_out, amount_in):

    quote_addr = Web3.to_checksum_address('0x61fFE014bA17989E743c5F6cB21bF9697530B21e')
    with open('abi/uni_quoter_v2.json') as f:
        uni_quoter_abi = json.load(f)

    quote_contract = w3.eth.contract(quote_addr, abi=uni_quoter_abi)

    with open('abi/ERC20.json') as f:
        erc_20_abi = json.load(f)
    
    token_in = Web3.to_checksum_address(token_in)
    token_out = Web3.to_checksum_address(token_out)

    token_in_contract = w3.eth.contract(address= token_in, abi=erc_20_abi)
    token_out_contract = w3.eth.contract(address= token_out, abi=erc_20_abi)

    token_in_decimals = 10 ** token_in_contract.functions.decimals().call()
    token_out_decimals = 10 ** token_out_contract.functions.decimals().call()

    token_in_symbol = token_in_contract.functions.symbol().call()
    token_out_symbol = token_out_contract.functions.symbol().call()

    amount_in = int( amount_in * token_in_decimals)


    quote_contract = w3.eth.contract(quote_addr, abi=uni_quoter_abi)


    #for index in range(0, len(sorted_matching_pools)):

    """

    pool_id_1 = sorted_matching_pools[0]['id']
    pool_fee_1 = int(sorted_matching_pools[0]['feeTier'])

    pool_id_2 = sorted_matching_pools[1]['id']
    pool_fee_2 = int(sorted_matching_pools[1]['feeTier'])
    """

    all_fees = [100, 500, 3000, 10000]
    combinations = list(itertools.combinations_with_replacement(all_fees, 2))

    for pool in sorted_matching_pools:
    

        for combo in combinations:

            if pool['token0'] == token_in:
                
                #QUOTE  PATH
                # Token_In  ->    X    ->    Y    -> Token_In
                path = eth_abi.packed.encode_packed(['address','uint24','address','uint24','address'], [token_in, combo[0], pool['token1']['id'], combo[1], token_in])
                
                amount_out, sqrtPriceX96After, initializedTicksCrossed, gasEstimate  = quote_contract.functions.quoteExactInput(
                    path,
                    amount_in
                ).call()

                print(f'{amount_in / token_in_decimals } {token_in_symbol}  --->   {amount_out / token_in_decimals}.')
                print("---")

                print()

                
            else:

                #QUOTE  PATH
                # Token_In  ->    X    ->    Y    -> Token_In
                path = eth_abi.packed.encode_packed(['address','uint24','address','uint24','address'], [token_in, combo[0], pool['token0']['id'], combo[1], token_in])
                
                amount_out, sqrtPriceX96After, initializedTicksCrossed, gasEstimate  = quote_contract.functions.quoteExactInput(
                    path,
                    amount_in
                ).call()

                print(f'{amount_in / token_in_decimals } {token_in_symbol}  --->   {amount_out / token_in_decimals} {token_in_symbol}.')
                print("---")

                print()



            if combo[0] != combo[1]:
                
                if pool['token0'] == token_in:
                    
                    #QUOTE  PATH
                    # Token_In  ->    X    ->    Y    -> Token_In
                    path = eth_abi.packed.encode_packed(['address','uint24','address','uint24','address'], [token_in, combo[1], pool['token1']['id'], combo[0], token_in])
                    
                    amount_out, sqrtPriceX96After, initializedTicksCrossed, gasEstimate  = quote_contract.functions.quoteExactInput(
                        path,
                        amount_in
                    ).call()

                    print(f'{amount_in / token_in_decimals } {token_in_symbol}  --->   {amount_out / token_in_decimals}.')
                    print("---")

                    print()

                    
                else:

                    #QUOTE  PATH
                    # Token_In  ->    X    ->    Y    -> Token_In
                    path = eth_abi.packed.encode_packed(['address','uint24','address','uint24','address'], [token_in, combo[1], pool['token0']['id'], combo[0], token_in])
                    
                    amount_out, sqrtPriceX96After, initializedTicksCrossed, gasEstimate  = quote_contract.functions.quoteExactInput(
                        path,
                        amount_in
                    ).call()

                    print(f'{amount_in / token_in_decimals } {token_in_symbol}  --->   {amount_out / token_in_decimals} {token_in_symbol}.')
                    print("---")

                    print()






def uni_best_routes_v3(token_in, token_out, amount_in):
    #print(f'Connected via HTTP: {w3.is_connected()}')
    #print("Connected to chain: ", w3.eth.chain_id)

    #sorted_matching_pools = get_pools(token_in, token_out)
    #get_possible_cycle(sorted_matching_pools, token_in, token_out, amount_in)

    get_best_quote(token_in, token_out, amount_in)

