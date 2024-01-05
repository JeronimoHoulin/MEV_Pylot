import sys
sys.path.append('./functions')
from get_whitelist_tokens import get_whitelist_tokens
from event_stream import stream_txns
from uni_v3 import get_pools
import json 

#The token you want to profit in (have a min of $10 worth for flash loan fees).
token_in = '0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619' #WETH
symb = 'WETH'
#Minimum expected profit for the txn to be executed. 
min_gain = 0.001


#Avoids salmonella tokens by fetching whitelist tokens only.
whitelist_tokens = get_whitelist_tokens()


with open('cached_pools/whitelist_pools.json') as f:
    whitelist_pools = json.load(f)


def loop_tokens(token_in, whitelist_tokens, min_gain, symb):
    all_whitelist_pools = []
    
    print("Fetching all whitelist pools...")
    print()

    ''' if not already cached...
    for token in whitelist_tokens:
        pools = get_pools(token_in, token)
        for pool in pools:
            all_whitelist_pools.append(pool['id'])
    '''

    for pool in whitelist_pools.keys():
        all_whitelist_pools.append(pool)
    
    stream_txns(all_whitelist_pools, min_gain, symb)

if __name__ == '__main__':
    loop_tokens(token_in, whitelist_tokens, min_gain, symb)
