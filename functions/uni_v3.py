import os
from dotenv import load_dotenv
from web3 import Web3
from web3.middleware import geth_poa_middleware
import json
import eth_abi.packed
import requests
import itertools
import time

from flashswap import flash_swap


#Connecting to ENV file
os.chdir('C:/Users/jeron/OneDrive/Desktop/Projects/Web3py') #Your CWD
load_dotenv()

HTTPS_PROVIDER = os.environ.get('HTTPS_PROVIDER')

#Creating Web3 instance
w3 = Web3(Web3.HTTPProvider(HTTPS_PROVIDER))

#inject middleware for POA chain Polygon
w3.middleware_onion.inject(geth_poa_middleware, layer=0)


def get_pools(token_in, token_out):

    #using API from uniswap docs:
    matching_pools = []

    token_in = token_in.lower()
    token_out = token_out.lower()

    all_pools = requests.get('https://cloudflare-ipfs.com/ipns/api.uniswap.org/v1/pools/v3/polygon-mainnet.json').json()


    for pool in all_pools:
        if pool['token0']['id'] in (token_in, token_out) and pool['token1']['id'] in (token_in, token_out):
            matching_pools.append(pool)  
    

    with open('cached_pools/whitelist_pools.json', 'r') as f:
        existing_whitelist_pools = json.load(f)

    for pool in matching_pools:

        if pool['id'] in existing_whitelist_pools:
            pass
        else:

            with open('abi/ERC20.json') as f:
                erc_20_abi = json.load(f)

            token_0 = Web3.to_checksum_address(pool['token0']['id'])
            token_1 = Web3.to_checksum_address(pool['token1']['id'])
            token_0_contract = w3.eth.contract(address= token_0, abi=erc_20_abi)
            token_1_contract = w3.eth.contract(address= token_1, abi=erc_20_abi)
            token_0_decimals = 10 ** token_0_contract.functions.decimals().call()
            token_1_decimals = 10 ** token_1_contract.functions.decimals().call()
            token_0_symbol = token_0_contract.functions.symbol().call()
            token_1_symbol = token_1_contract.functions.symbol().call()

            pool_adrs = pool['id']

            existing_whitelist_pools[f'{pool_adrs}'] = {
                'token0': pool['token0']['id'],
                'token1': pool['token1']['id'],
                'fee': pool['feeTier'],
                'token0_decimals': token_0_decimals,
                'token1_decimals': token_1_decimals,
                'token0_symbol': token_0_symbol,
                'token1_symbol': token_1_symbol
            }

            newData = json.dumps(existing_whitelist_pools, indent=4)
            with open('cached_pools/whitelist_pools.json', 'w') as f:
                f.write(newData)


    return matching_pools




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




#used for mannually checkingn token whitelist 1 by 1
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


    max_amount = 10*amount0

    if len(combinations) > 0:

        all_profitable_combos = {}

        while amount0 < max_amount:

            #print(f'Trying with {amount0 / token0_decimals}')

            for combo in combinations:


                if combo[0] == combo[1]: #same pool...
                    pass

                else:

                    #QUOTE  PATH
                    path = eth_abi.packed.encode_packed(['address','uint24','address','uint24','address'], [token0, combo[0], token1, combo[1], token0])
                    
                    amount_first  = quote_contract.functions.quoteExactInput(
                        path,
                        amount0
                    ).call()[0]


                    if amount_first/token0_decimals > ( amount0 / token0_decimals):
                        '''
                        print(f'From p1: {combo[0]} to p3: {combo[1]}')
                        print()
                        print(f'{amount0 / token0_decimals} {token0_symbol} -> {amount_first / token1_decimals} {token1_symbol}.')
                        print(f'{amount_first / token1_decimals} {token1_symbol} -> {amount_first/token0_decimals} {token0_symbol}.')
                        print()
                        '''

                        all_profitable_combos[f'{combo[0]},{combo[1]}'] = amount0 / token0_decimals

                        #flash_swap(token1, combo[0], combo[1], amount0)
                        #break



                    ################### OTHER WAY AROUND POOL2 -> POOL1

                    #QUOTE  PATH
                    path = eth_abi.packed.encode_packed(['address','uint24','address','uint24','address'], [token0, combo[1], token1, combo[0], token0])
                    
                    amount_first  = quote_contract.functions.quoteExactInput(
                        path,
                        amount0
                    ).call()[0]


                    if amount_first/token0_decimals > ( amount0 / token0_decimals):
                        '''
                        print(f'From p1: {combo[1]} to p3: {combo[0]}')
                        print()
                        print(f'{amount0 / token0_decimals} {token0_symbol} -> {amount_first / token1_decimals} {token1_symbol}.')
                        print(f'{amount_first / token1_decimals} {token1_symbol} -> {amount_first/token0_decimals} {token0_symbol}.')
                        print()
                        '''

                        #flash_swap(token1, combo[1], combo[0], amount0)
                        #break

                        all_profitable_combos[f'{combo[1]},{combo[0]}'] = amount0 / token0_decimals


            
            amount0 = int(1.5*amount0)

        if len(all_profitable_combos):
            max_combo = str(max(all_profitable_combos)).split(',')
            print(f'Pool combo: {max_combo}')
            print(all_profitable_combos[f'{max_combo[0]},{max_combo[1]}']) 
            print('Optimal Amount of WETH for Swap:')
            #optimal_amount_in = int(all_profitable_combos[f'{max_combo[0]},{max_combo[1]}'] * token0_decimals)
            #flash_swap(token1, max_combo[0], max_combo[1], optimal_amount_in)
        else:
            pass



#used for new headers
async def get_possible_flashswap(used_pool, weth_amt):

    start = time.time()
    
    if used_pool['token0_symbol'] == 'WETH':
        weth_token = Web3.to_checksum_address(used_pool['token0'])
        weth_decimals = used_pool['token0_decimals']
        weth_symbol = used_pool['token0_symbol']
        othr_token = Web3.to_checksum_address(used_pool['token1'])
        #othr_decimals = used_pool['token1_decimals']
        othr_symbol = used_pool['token1_symbol']
    else:
        weth_token = Web3.to_checksum_address(used_pool['token1'])
        weth_decimals = used_pool['token1_decimals']
        weth_symbol = used_pool['token1_symbol']
        othr_token = Web3.to_checksum_address(used_pool['token0'])
        #othr_decimals = used_pool['token0_decimals']
        othr_symbol = used_pool['token0_symbol']


    quote_addr = Web3.to_checksum_address('0x61fFE014bA17989E743c5F6cB21bF9697530B21e')
    with open('abi/uni_quoter_v2.json') as f:
        uni_quoter_abi = json.load(f)
    quote_contract = w3.eth.contract(quote_addr, abi=uni_quoter_abi)


    fee0 = int(used_pool['fee'])
    with open('cached_pools/whitelist_pools.json') as f:
        whitelist_pools = json.load(f)


    all_fees = [] #100, 500, 3000, 10000

    for value in whitelist_pools.values():
        if othr_symbol in (value['token0_symbol'], value['token1_symbol']):
            all_fees.append(int(value['fee']))


    all_profitable_combos = {}


    if weth_amt < 0: #WETH SOLD IN POOL FEE0

        for fee in all_fees:

            amount0 = int( weth_amt * weth_decimals * 0.2) # start by testing 20% of the traded amount in pool x
            max_amount = int(1.5 * weth_decimals)        #increase test amount by 2 untill 100% of traded amount. 

            if fee == fee0: #Same pool
                pass
            else:

                amount0 = int(-1 * amount0)

                while amount0 < max_amount:

                    #print(f"Going over pool {fee}, see if it's profitable with a amt { - amount0 / weth_decimals}...")

                    # Buy in recently underpriced fee0 and sell in fee
                    path = eth_abi.packed.encode_packed(['address','uint24','address','uint24','address'], [weth_token, fee0, othr_token, fee, weth_token])
                    
                    amount_first =  quote_contract.functions.quoteExactInput(
                        path,
                        amount0
                    ).call()[0]


                    if amount_first > 0: #* amount0 / weth_decimals:
                        
                        #print(f'From pool fee: {fee0} to pool: {fee}')
                        #print(f'{amount0 / weth_decimals} {weth_symbol} ->  {othr_symbol} -> {amount_first/weth_decimals} {weth_symbol}.')

                        profit = ( amount_first - amount0 * 0.997 ) / weth_decimals #FLASH LOAN FEE 0.03%
                        all_profitable_combos[f'{fee0},{fee},{amount0}'] = profit
                    
                    amount0 = 2 * amount0


    else: #WETH BOUGHT IN POOL FEE0

        for fee in all_fees:

            amount0 = int( weth_amt * weth_decimals * 0.2) # start by testing 20% of the traded amount in pool x
            max_amount = int(1.5 * weth_decimals)        #increase test amount by 2 untill 100% of traded amount. 

            if fee == fee0:
                pass
            else:
                while amount0 < max_amount:

                    #print(f"Going over pool {fee}, see if it's profitable with a amt {amount0 / weth_decimals}...")

                    # Buy in fee and sell in recently overpriced pool fee0
                    path = eth_abi.packed.encode_packed(['address','uint24','address','uint24','address'], [weth_token, fee, othr_token, fee0, weth_token])
                    
                    amount_first  = quote_contract.functions.quoteExactInput(
                        path,
                        amount0
                    ).call()[0]


                    if amount_first > 0: # * amount0 / weth_amt:
                        
                        #print(f'From pool fee: {fee} to pool: {fee0}')
                        #print(f'{amount0 / weth_decimals} {weth_symbol} ->  {othr_symbol} -> {amount_first/weth_decimals} {weth_symbol}.')
                        profit = ( amount_first - amount0 * 0.997 ) / weth_decimals #FLASH LOAN FEE 0.03%
                        all_profitable_combos[f'{fee},{fee0},{amount0}'] = profit

                    amount0 = 2 * amount0


    if len(all_profitable_combos) > 0:

        max_combo = str(max(all_profitable_combos)).split(',')
        max_profit = int(all_profitable_combos[f'{max_combo[0]},{max_combo[1]},{max_combo[2]}'] * weth_decimals)
        print(f"Profit: {max_profit /  weth_decimals} WETH.")


        if max_profit > 0.001:
            #print('Optimal Amount of WETH INPUT:')
            #print(max_combo[2])
            print("Started a flashswap")
            flash_swap(othr_token, max_combo[0], max_combo[1], max_combo[2])
            end = time.time()
            print("END Timer:")
            print(end-start)
            return True
        
        else:
            False

    else:
        #end = time.time()
        #print("END Timer:")
        #print(end-start)
        print("No possible combinations...")
        return False
            









def uni_best_routes_v3(token_in, token_out, amount_in):


    #get_best_quote(token_in, token_out, amount_in)


    get_imbalanced_pools(token_in, token_out, amount_in)


    #print("Getting flashswap...")
    #get_possible_flashswap(token_in, token_out, amount_in, fee0)



