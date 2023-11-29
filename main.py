import sys
sys.path.append('./functions')
from get_whitelist_tokens import get_whitelist_tokens
from event_stream import stream_txns
from uni_v3 import get_pools

#The token you want to profit in (have a min of $10 worth for flash loan fees).
token_in = '0x7ceb23fd6bc0add59e62ac25578270cff1b9f619' #WETH
#Minimum expected profit for the txn to be executed. 
min_gain = 0.002


#Avoids salmonella tokens by fetching whitelist tokens only.
whitelist_tokens = get_whitelist_tokens()

def loop_tokens(token_in, whitelist_tokens, min_gain):
    all_whitelist_pools = []
    print("Fetching all whitelist pools...")
    print()
    for token in whitelist_tokens:
        pools = get_pools(token_in, token)
        for pool in pools:
            all_whitelist_pools.append(pool['id'])
    
    stream_txns(all_whitelist_pools, min_gain)

if __name__ == '__main__':
    loop_tokens(token_in, whitelist_tokens, min_gain)
