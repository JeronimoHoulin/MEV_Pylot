import sys
sys.path.append('./functions')

from get_whitelist_tokens import get_whitelist_tokens
from one_inch import get_quote
from uni_prices import uni_best_routes_v3




token_in = '0x7ceb23fd6bc0add59e62ac25578270cff1b9f619'  #WETH
amount_in = 1

#Avoids salmonella tokens easily...
whitelist_tokens = get_whitelist_tokens()



def loop_tokens(token_in, whitelist_tokens, amount_in):

    for token_through in whitelist_tokens:

        print(f"Getting imbalances for token: {token_through}...")

        if token_through == token_in or token_through == '0x0000000000000000000000000000000000001010': 
            pass
        else:
            uni_best_routes_v3(token_in=token_in, token_out=token_through, amount_in=amount_in)


    """

    for token_out in whitelist_tokens:

        amount_out = get_quote(token_in, token_out, amount_in) #1INCH API

        uni_best_routes_v3(token_in=token_out, token_out=token_in, amount_in=amount_out)


    """



if __name__ == '__main__':
    loop_tokens(token_in, whitelist_tokens, amount_in)


