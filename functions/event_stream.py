import asyncio
import json
from web3.middleware import geth_poa_middleware
from web3 import Web3
from websockets import connect
import os
from dotenv import load_dotenv

from uni_v3 import get_possible_flashswap

import eth_abi



os.chdir('C:/Users/jeron/OneDrive/Desktop/Projects/Web3py') #Your CWD
load_dotenv()

infura_ws_url = os.environ.get('WSS_PROVIDER')
infura_http_url = os.environ.get('HTTPS_PROVIDER')

web3 = Web3(Web3.HTTPProvider(infura_http_url))
web3.middleware_onion.inject(geth_poa_middleware, layer=0)
print()
print("Connected to chain: ", web3.eth.chain_id)
print()

WETH = '0x7ceb23fd6bc0add59e62ac25578270cff1b9f619'  #WETH


#DECODES SWAP EVENTS IN UNISWAP V3 POOLS
def decode_log_data(data):
    types = ['int256', 'int256', 'uint160', 'uint128', 'int24']
    names = ['amount0', 'amount1', 'sqrtPriceX96', 'liquidity', 'int24']
    bb = bytes.fromhex(data[2:]) # Remember to jump over 0x...                                             
    values = eth_abi.decode(types, bb)                                                                    
    return dict(zip(names, values))




async def get_event(all_whitelist_pools, min_gain, loop):

    all_pools = all_whitelist_pools
    params = {"jsonrpc": "2.0", "id": 1, "method": "eth_subscribe", "params": ["logs", {"address":  all_pools}]}

    async with connect(infura_ws_url) as ws:
        await ws.send(json.dumps(params))

        print('Listening to pool events...')

        while True:

            try:

                message = await asyncio.wait_for(ws.recv(), timeout= 10) #Polygon takes 2 sec for block confir.
                response = json.loads(message)

                ## STREAM DATA:
                if 'params' in response.keys():


                    data = response['params']['result']['data']
                    used_pool = response['params']['result']['address'].lower()
                    """
                    event Swap(
                        address indexed sender,
                        address indexed recipient,
                        int256 amount0,
                        int256 amount1,
                        uint160 sqrtPriceX96,
                        uint128 liquidity,
                        int24 tick
                    );
                    """
                    decoded_data = decode_log_data(data)

                    with open('cached_pools/whitelist_pools.json') as f:
                        whitelist_pools = json.load(f)

                    pool_meta = whitelist_pools[f'{used_pool}']

                    if pool_meta['token0_symbol'] == 'WETH':
                        weth_amt = decoded_data['amount0'] / pool_meta['token0_decimals']
                        other_amt = decoded_data['amount1'] / pool_meta['token1_decimals']
                        other_symb = pool_meta['token1_symbol']
                    else:
                        weth_amt = decoded_data['amount1'] / pool_meta['token1_decimals']
                        other_amt = decoded_data['amount0'] / pool_meta['token0_decimals']
                        other_symb = pool_meta['token0_symbol']

                    if weth_amt > 0.001:
                        print('--------------------- EVT --------------------------')
                        '''
                        print(f'Utilized pool: [{used_pool}]')
                        print(f'Amount traded: {weth_amt} WETH')
                        print(f'                {other_amt} {other_symb}')

                        print('Tx hash: ' + response['params']['result']['transactionHash'])
                        print('-----------------------------------------------')
                        '''
                        
                        result = await get_possible_flashswap(pool_meta, weth_amt, min_gain)
                        
                        if result == True:
                            loop.close()
                            break



                else:
                    pass

            
            except:
                pass


def stream_txns(all_whitelist_pools, min_gain):
    loop = asyncio.get_event_loop()
    
    while True:
        loop.run_until_complete(get_event(all_whitelist_pools, min_gain, loop))

