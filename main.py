import sys
sys.path.append('./functions')

from get_whitelist_tokens import get_whitelist_tokens
from one_inch import get_quote
from uni_v3 import get_imbalanced_pools
from new_heads import stream_txns



WETH = '0x7ceb23fd6bc0add59e62ac25578270cff1b9f619'  #WETH
amount_min = 0.1



#Avoids salmonella tokens easily...
whitelist_tokens = get_whitelist_tokens()


def loop_tokens(token_in, whitelist_tokens, amount_in):

    while True:

        print()
        print("Re-Running...")

        for token_through in whitelist_tokens:

            print(f"Getting imbalances for token: {token_through}")

            if token_through == token_in or token_through == '0x0000000000000000000000000000000000001010': 
                pass
            else:
                get_imbalanced_pools(token0=token_in, token1=token_through, amount0=amount_in)


    """

    for token_out in whitelist_tokens:

        amount_out = get_quote(token_in, token_out, amount_in) #1INCH API

        uni_best_routes_v3(token_in=token_out, token_out=token_in, amount_in=amount_out)


    """




def imbalance_search():

    '''NEW HEADS'''
    stream_txns()



if __name__ == '__main__':

    loop_tokens(WETH, whitelist_tokens, amount_min)
    #imbalance_search()


