import os
from dotenv import load_dotenv
from web3 import Web3
from web3.middleware import geth_poa_middleware
import json
import eth_abi.packed
import requests
import time
import datetime as dt
from flashswap import flash_swap, dodo_loan_swap
from one_inch import get_quote, get_swap_callback

#Connecting to ENV file
os.chdir('C:/Users/jeron/OneDrive/Desktop/Projects/Web3py') #Your CWD
load_dotenv()

HTTPS_PROVIDER = os.environ.get('HTTPS_PROVIDER')
DEPLOYED_DODO_SWAP = os.environ.get('DEPLOYED_DODO_SWAP')

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


async def get_uni_flashswap(used_pool, in_amt, min_gain, symb):

    start = time.time()
    
    if used_pool['token0_symbol'] == symb:
        in_token = Web3.to_checksum_address(used_pool['token0'])
        in_decimals = used_pool['token0_decimals']
        #in_symbol = used_pool['token0_symbol']
        othr_token = Web3.to_checksum_address(used_pool['token1'])
        #othr_decimals = used_pool['token1_decimals']
        othr_symbol = used_pool['token1_symbol']
    else:
        in_token = Web3.to_checksum_address(used_pool['token1'])
        in_decimals = used_pool['token1_decimals']
        #in_symbol = used_pool['token1_symbol']
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


    if in_amt < 0: #WETH SOLD IN POOL FEE0

        for fee in all_fees:

            amount0 = int( in_amt * in_decimals * 0.5) # start by testing 20% of the traded amount in pool x
            max_amount = int(in_decimals)        #increase test amount by 2 untill 100% of traded amount. 

            if fee == fee0: #Same pool
                pass
            else:

                amount0 = int(-1 * amount0)   #convert to positive amt (-0.1 WETH => 0.1 WETH)

                while amount0 < max_amount:

                    #print(f"Going over pool {fee}, see if it's profitable with a amt { - amount0 / in_decimals}...")

                    # Buy in recently underpriced fee0 and sell in fee
                    path = eth_abi.packed.encode_packed(['address','uint24','address','uint24','address'], [in_token, fee0, othr_token, fee, in_token])
                    
                    amount_first =  quote_contract.functions.quoteExactInput(
                        path,
                        amount0
                    ).call()[0]


                    if amount_first > 0.5 * amount0:
                        
                        #print(f'From pool fee: {fee0} to pool: {fee}')
                        #print(f'{amount0 / in_decimals} {in_symbol} ->  {othr_symbol} -> {amount_first/in_decimals} {in_symbol}.')

                        profit = ( amount_first - amount0 * 0.997 ) / in_decimals #FLASH LOAN FEE 0.03%
                        all_profitable_combos[f'{fee0},{fee},{amount0}'] = profit
                    
                    amount0 = 2 * amount0


    else: #WETH BOUGHT IN POOL FEE0

        for fee in all_fees:

            amount0 = int( in_amt * in_decimals * 0.5) # start by testing 20% of the traded amount in pool x
            max_amount = int(in_decimals)        #increase test amount by 2 untill 100% of traded amount. 

            if fee == fee0:
                pass
            else:
                while amount0 < max_amount:

                    #print(f"Going over pool {fee}, see if it's profitable with a amt {amount0 / in_decimals}...")

                    # Buy in fee and sell in recently overpriced pool fee0
                    path = eth_abi.packed.encode_packed(['address','uint24','address','uint24','address'], [in_token, fee, othr_token, fee0, in_token])
                    
                    amount_first  = quote_contract.functions.quoteExactInput(
                        path,
                        amount0
                    ).call()[0]


                    if amount_first > 0.5 * amount0:
                        
                        #print(f'From pool fee: {fee} to pool: {fee0}')
                        #print(f'{amount0 / in_decimals} {in_symbol} ->  {othr_symbol} -> {amount_first/in_decimals} {in_symbol}.')
                        profit = ( amount_first - amount0 * 0.997 ) / in_decimals #FLASH LOAN FEE 0.03%
                        all_profitable_combos[f'{fee},{fee0},{amount0}'] = profit

                    amount0 = 2 * amount0


    if len(all_profitable_combos) > 0:

        max_combo = str(max(all_profitable_combos)).split(',')
        max_profit = int(all_profitable_combos[f'{max_combo[0]},{max_combo[1]},{max_combo[2]}'] * in_decimals)
        if max_profit / in_decimals > min_gain:
            print(f"Expected profit: {max_profit /  in_decimals} {symb}.")
            print("Started a flashswap...")
            #print(f'params: [{othr_token, max_combo[0], max_combo[1], max_combo[2]}]')
            flash_swap(in_token, symb, othr_token, max_combo[0], max_combo[1], max_combo[2])
            end = time.time()
            print("END Timer:")
            print(end-start)
            return True
        
        else:
            return False

    else:
        #end = time.time()
        #print("END Timer:")
        #print(end-start)
        #print("No possible combinations...")
        return False
            


async def uni_quick_flashwsap(used_pool, in_amount, other_amount, min_gain, symb):
    '''    
    traded_eth = 0.6
    used_pool, in_amount, other_amount, min_gain, symb = {
            "token0": "0x2791bca1f2de4661ed88a30c99a7a9449aa84174",
            "token1": "0x7ceb23fd6bc0add59e62ac25578270cff1b9f619",
            "fee": "500",
            "token0_decimals": 1000000,
            "token1_decimals": 1000000000000000000,
            "token0_symbol": "USDC",
            "token1_symbol": "WETH"
        }, -traded_eth, traded_eth*2030, 0, "WETH"
    '''
    if used_pool['token0_symbol'] == symb:
        in_token = Web3.to_checksum_address(used_pool['token0'])
        in_decimals = used_pool['token0_decimals']
        in_symbol = used_pool['token0_symbol']
        othr_token = Web3.to_checksum_address(used_pool['token1'])
        othr_decimals = used_pool['token1_decimals']
        othr_symbol = used_pool['token1_symbol']
    else:
        in_token = Web3.to_checksum_address(used_pool['token1'])
        in_decimals = used_pool['token1_decimals']
        in_symbol = used_pool['token1_symbol']
        othr_token = Web3.to_checksum_address(used_pool['token0'])
        othr_decimals = used_pool['token0_decimals']
        othr_symbol = used_pool['token0_symbol']

    #UNISWAPV3 Quoterv2.
    """ Router to use in smart contract: 0xE592427A0AEce92De3Edee1F18E0157C05861564"""
    uni_quote_addr = Web3.to_checksum_address('0x61fFE014bA17989E743c5F6cB21bF9697530B21e')
    with open('abi/uni_quoter_v2.json') as f:
        uni_quoter_abi = json.load(f)
    uni_quote_contract = w3.eth.contract(uni_quote_addr, abi=uni_quoter_abi)

    #SushiSwapV3 NO V3 POOLS IN SUSHISWAP.. look at factory: https://github.com/sushiswap/v3-periphery/tree/master/deployments/polygon
    #This REKT is why: https://rekt.news/sushi-yoink-rekt/

    #Quickswap Quoter:
    """Router to use in smart contract: 0xf5b509bB0909a69B1c207E495f687a596C168E12"""
    quick_quote_addr = Web3.to_checksum_address('0xa15F0D7377B2A0C0c10db057f641beD21028FC89')
    with open('abi/quick_quoter_v2.json') as f:
        quick_quoter_abi = json.load(f)
    #quick_quote_contract = w3.eth.contract(quick_quote_addr, abi=quick_quoter_abi)

    fee0 = int(used_pool['fee'])
    #all_fees = [100, 500, 3000, 10000]

    if in_amount < 0: # - TOKEN means the token has been BOUGHT (i.e. taken out of pool)  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

            
        other_amt = int(other_amount * othr_decimals)
        in_amt =  - int(in_amount * in_decimals)

        # Single Hop on Quickswap:
        ''' Buy cheap on QS '''

        '''
        try: 
            path = eth_abi.packed.encode_packed(['address','address'], [othr_token, in_token])
            res = quick_quote_contract.functions.quoteExactInput(
                path,
                other_amt
            ).call()

            in_token_amt = res[0]
            fee = res[1]

            print(f"Swap {other_amt / othr_decimals} {othr_symbol} for {in_token_amt / in_decimals} {in_symbol} on QuickSwap (fee: {fee}).")
        except:
            print("QuickSwap pool not supported...")

        '''
        
        #in_token_amt = get_quote(othr_token, in_token, other_amt/othr_decimals)
        in_token_amt, call_data = get_swap_callback(othr_token, in_token, other_amt, DEPLOYED_DODO_SWAP) #DODO CONTRACT WILL MAKE THE 1INCH SWAPS
        in_token_amt = int(in_token_amt)
        #print(f"Swap {other_amt / othr_decimals} {othr_symbol} for {in_token_amt / in_decimals} {in_symbol} on OneInch.")

        #Single Hop on Uniswap:
        #print(f" -> Original {in_symbol} bought in poolfee: {fee0}")
        #for fee in all_fees:
        ''' Sell expensive on US '''
        #print(in_token, fee0, othr_token)
        path = eth_abi.packed.encode_packed(['address','uint24','address'], [in_token, fee0, othr_token])
        
        amount_other_out =  uni_quote_contract.functions.quoteExactInput(
            path,
            in_token_amt
        ).call()[0]


        #print(f"Swap {in_token_amt / in_decimals} {in_symbol} for {amount_other_out / othr_decimals} {othr_symbol} on UniSwap (fee: {fee0}).")
        #print()
        profit = (amount_other_out - other_amt) / othr_decimals

        if(profit > 2):

            if othr_symbol in ('USDC', 'USDT'):
                dodo_pool = w3.to_checksum_address('0x813FddecCD0401c4Fa73B092b074802440544E52')
            elif othr_symbol == 'WBTC':
                dodo_pool = w3.to_checksum_address('0x3D9d58cF6B1dD8Be3033CE8865F155FaC16186Cc')
            else:
                dodo_pool = None
                print(f"Get a DODO pool for {othr_symbol} token")
            if dodo_pool != None:
                print(f"Profit: {profit} !!")
                print(f'Initiating Flash Loan Arbitrage with {other_amt/othr_decimals} {othr_symbol}.')
                dodo_loan_swap(dodo_pool, othr_token, in_token, other_amt, in_token_amt, fee0, call_data)
                # flashLoanPool,  loanToken,  throughToken,  loanAmount,  minOutOneInch,  unifee,   memory _dataOneInch



