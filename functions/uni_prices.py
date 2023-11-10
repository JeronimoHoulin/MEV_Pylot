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

    '''
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

        if pool:
            all_pools.append(pool)
        else:
            pass

    return all_pools
    '''


    #using API from uniswap docs:
    matching_pools = []

    token_in = token_in.lower()
    token_out = token_out.lower()

    all_pools = requests.get('https://cloudflare-ipfs.com/ipns/api.uniswap.org/v1/pools/v3/polygon-mainnet.json').json()


    for pool in all_pools:
        if pool['token0']['id'] in (token_in, token_out) and pool['token1']['id'] in (token_in, token_out) and pool['tvlUSD'] > 1000:
            matching_pools.append(pool)  


    #print(f'Found {len(matching_pools)} pools that have either Token0 and Token1.')
    #print()
    #ORdering by tvl
    sorted_matching_pools = sorted(matching_pools, key=lambda d: d['tvlUSD'], reverse=True) 


    return sorted_matching_pools







def get_best_quote(token_in, token_out, amount_in):

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
    print(f'Fetching best sell prices on Uni for {amount_in } {token_in_symbol}...')
    amount_in = int( amount_in * token_in_decimals)


    all_pools = get_pools(token_in, token_out)


    for pool in all_pools:

        if pool['feeTier']:
        
            #QUOTE  PATH
            # Token_In  ->    X    ->    Y    -> Token_In
            path = eth_abi.packed.encode_packed(['address','uint24','address'], [token_in, int(pool['feeTier']), token_out])
            
            amount_out  = quote_contract.functions.quoteExactInput(
                path,
                amount_in
            ).call()[0]

            print()
            print(f'You can flip it for {amount_out / token_out_decimals} {token_out_symbol}')
            print()

        else:
            payload = (
                token_in, #address tokenIn;
                token_out, #address tokenOut;
                amount_in, #uint256 amountIn;
                100, #uint24 fee;
                0, #uint160 sqrtPriceLimitX96;
            )
            resp = quote_contract.functions.quoteExactInputSingle(
                    payload
                ).call()
                    
            amount_out = resp[0]
            print()
            print(f'You can flip it for {amount_out / token_out_decimals} {token_out_symbol}')




####################################### TESTING #######################################



def get_imbalanced_pools(token0, token1, amount0):

    quote_addr = Web3.to_checksum_address('0x61fFE014bA17989E743c5F6cB21bF9697530B21e')
    with open('abi/uni_quoter_v2.json') as f:
        uni_quoter_abi = json.load(f)

    quote_contract = w3.eth.contract(quote_addr, abi=uni_quoter_abi)

    with open('abi/ERC20.json') as f:
        erc_20_abi = json.load(f)
    
    token0 = Web3.to_checksum_address(token0)
    token1 = Web3.to_checksum_address(token1)
    token0_contract = w3.eth.contract(address= token0, abi=erc_20_abi)
    token1_contract = w3.eth.contract(address= token1, abi=erc_20_abi)
    token0_decimals = 10 ** token0_contract.functions.decimals().call()
    token1_decimals = 10 ** token1_contract.functions.decimals().call()
    token0_symbol = token0_contract.functions.symbol().call()
    token1_symbol = token1_contract.functions.symbol().call()
    amount0 = int( amount0 * token0_decimals)


    all_fees = [] #100, 500, 3000, 10000

    all_pools = get_pools(token0, token1)

    for pool in all_pools:
        all_fees.append(int(pool['feeTier']))

    
    combinations = list(itertools.combinations_with_replacement(all_fees, 2))

    if len(combinations) > 0:

        for combo in combinations:

            if combo[0] == combo[1]: #same pool...
                pass

            else:

                #QUOTE  PATH
                path = eth_abi.packed.encode_packed(['address','uint24','address'], [token0, combo[0], token1])
                
                amount_first  = quote_contract.functions.quoteExactInput(
                    path,
                    amount0
                ).call()[0]



                #QUOTE  PATH
                path = eth_abi.packed.encode_packed(['address','uint24','address'], [token1, combo[1], token0])
                
                amount_final  = quote_contract.functions.quoteExactInput(
                    path,
                    amount_first
                ).call()[0]

                if amount_final/token0_decimals > int(amount0 / token0_decimals) - 0.1:
                    print()
                    print(f'{amount0 / token0_decimals} {token0_symbol} -> {amount_first / token1_decimals} {token1_symbol}.')
                    print(f'{amount_first / token1_decimals} {token1_symbol} -> {amount_final/token0_decimals} {token0_symbol}.')
                    print()

                ################### OTHER WAY AROUND POOL2 -> POOL1



                #QUOTE  PATH
                path = eth_abi.packed.encode_packed(['address','uint24','address'], [token0, combo[1], token1])
                
                amount_first  = quote_contract.functions.quoteExactInput(
                    path,
                    amount0
                ).call()[0]



                #QUOTE  PATH
                path = eth_abi.packed.encode_packed(['address','uint24','address'], [token1, combo[0], token0])
                
                amount_final  = quote_contract.functions.quoteExactInput(
                    path,
                    amount_first
                ).call()[0]


                if amount_final/token0_decimals > int(amount0 / token0_decimals) - 0.1:
                    print()
                    print(f'{amount0 / token0_decimals} {token0_symbol} -> {amount_first / token1_decimals} {token1_symbol}.')
                    print(f'{amount_first / token1_decimals} {token1_symbol} -> {amount_final/token0_decimals} {token0_symbol}.')
                    print()







####################################### TESTING #######################################






def uni_best_routes_v3(token_in, token_out, amount_in):


    #get_best_quote(token_in, token_out, amount_in)


    get_imbalanced_pools(token_in, token_out, amount_in)



