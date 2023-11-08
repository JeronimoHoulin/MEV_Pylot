from one_inch import get_quote
from uni_prices import uni_best_routes_v3


token_in = '0xc2132d05d31c914a87c6611c10748aeb04b58e8f'  #USDT
#token_out = '0x7ceb23fd6bc0add59e62ac25578270cff1b9f619' #WETH
amount_in = 1000 #Stablecoins

#Avoids salmonella tokens easily...
whitelist_tokens = [
    '0x7ceb23fd6bc0add59e62ac25578270cff1b9f619', #WETH
    '0x1bfd67037b42cf73acf2047067bd4f2c47d9bfd6', #WBTC
    '0x6f8a06447ff6fcf75d803135a7de15ce88c1d4ec', #SHIB
    '0xb33eaad8d922b1083446dc23f610c2567fb5180f', #UNI
    '0xc3c7d422809852031b44ab29eec9f1eff2a58756', #LDO
    '0x6f7C932e7684666C9fd1d44527765433e01fF61d', #MRK
    '0xBbba073C31bF03b8ACf7c28EF0738DeCF3695683', #SAND
    ]

def loop_tokens(token_in, whitelist_tokens, amount_in):

    for token_out in whitelist_tokens:

        amount_out = get_quote(token_in, token_out, amount_in)

        uni_best_routes_v3(token_in=token_out, token_out=token_in, amount_in=amount_out)



if __name__ == '__main__':
    loop_tokens(token_in, whitelist_tokens, amount_in)


