from web3 import Web3
import asyncio
from web3.middleware import geth_poa_middleware
from websockets import connect
import time


#Note there are some issues with older websocket libraries soooo do the following: 
#pip install --upgrade web3
#pip install --upgrade websockets
#--------------------------Connection Setup stuff -------------------------------#
#INFURA_WS = 'wss://mainnet.infura.io/ws/v3/7e452892f2204d6a90e814c4a03a7b1d'
CHAIN_STACK_WS = 'wss://polygon-mainnet.core.chainstack.com/ws/98a90e3b50b1aeb917b04bb3303b5e83'
#POLYGON_WS = 'wss://rpc-mainnet.matic.network'
#INFURA_HTTP = 'https://polygon-mainnet.infura.io/v3/7e452892f2204d6a90e814c4a03a7b1d'



web3 = Web3(Web3.WebsocketProvider(CHAIN_STACK_WS))
print(f'Connected via WS: {web3.is_connected()}')
#inject middleware for POA chain Polygon
web3.middleware_onion.inject(geth_poa_middleware, layer=0)
print("Connected to chain: ", web3.eth.chain_id)

uni_router_v1 = '0xE592427A0AEce92De3Edee1F18E0157C05861564'
#METHODS TO MONITOR
exactInput = '0xc04b8d59'
exactInputSingle = '0x414bf389'
exactOutput = '0xf28c0498'
exactOutputSingle = '0xdb3e2198'


#-------------------------- Filter New Block Headers -------------------------------#


def handle_event(event):
        
    block_hash = event.hex()
    block = web3.eth.get_block(block_hash)

    print('Geting block: ' + str(block['number']))

    txns = block['transactions']

    for txn in txns:
        try:
            txn = web3.eth.get_transaction(txn)
            if txn['to'] and txn['to'] == uni_router_v1:
                
                #exactInputSingle || exactOutputSingle
                if txn['input'][0: 10] in (exactInputSingle, exactOutputSingle):
                    print('Found an exact in/out SINGLE!')
                    print(txn['hash'].hex())
                    token0 = '0x'+txn['input'][34:74]
                    token1 = '0x'+txn['input'][98:138]
                    print(f'token0: {token0}')
                    print(f'token1: {token1}')


                #exactInput // exactOutput
                if txn['input'][0: 10] in (exactInput, exactOutput):
                    print('Found an exact in/out!')
                    print(txn['hash'].hex())
                    token0 = '0x'+txn['input'][34:74]
                    token1 = '0x'+txn['input'][98:138]
                    print(f'token0: {token0}')
                    print(f'token1: {token1}')

        except Exception as e:
            pass
            #print(f'error occurred: {e}')


def log_loop(event_filter, poll_interval):
    while True:
        for event in event_filter.get_new_entries():
            handle_event(event)
        time.sleep(poll_interval)

def main():
    block_filter = web3.eth.filter('latest')
    log_loop(block_filter, 2)

if __name__ == '__main__':
    main()