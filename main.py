from one_inch import get_quote
from uni_prices import uni_best_routes_v3


# some_file.py
import sys
# caution: path[0] is reserved for script path (or '' in REPL)
sys.path.append('./functions')

from get_whitelist_tokens import get_whitelist_tokens




token_in = '0xc2132d05d31c914a87c6611c10748aeb04b58e8f'  #USDT
#token_out = '0x7ceb23fd6bc0add59e62ac25578270cff1b9f619' #WETH
amount_in = 1000 #Stablecoins

#Avoids salmonella tokens easily...
whitelist_tokens = get_whitelist_tokens()



def loop_tokens(token_in, whitelist_tokens, amount_in):

    for token_out in whitelist_tokens:

        amount_out = get_quote(token_in, token_out, amount_in)

        uni_best_routes_v3(token_in=token_out, token_out=token_in, amount_in=amount_out)



if __name__ == '__main__':
    loop_tokens(token_in, whitelist_tokens, amount_in)


