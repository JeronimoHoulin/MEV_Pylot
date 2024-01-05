#Uniswap on Polygon

from web3 import Web3
from web3.middleware import geth_poa_middleware
import time
#from eth_abi import encode_abi

INFURA_HTTP = 'https://polygon-mainnet.infura.io/v3/7e452892f2204d6a90e814c4a03a7b1d'

w3 = Web3(Web3.HTTPProvider(INFURA_HTTP))
print(f'Connected via HTTP: {w3.is_connected()}')

#-------------------------- Injecting middleware for Polygon  -------------------------------#

#inject middleware
w3.middleware_onion.inject(geth_poa_middleware, layer=0)
chain_id = 137 # Polygon Mainnet ID
account = {
    'private_key': '',
    'address':  Web3.to_checksum_address('0xaCd29F685C3bDf33588Aa90Bb65A69B4b098e62F') 
   }

