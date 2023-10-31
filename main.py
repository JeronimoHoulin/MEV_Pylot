from one_inch import get_quote

token_in = '0x53e0bca35ec356bd5dddfebbd1fc0fd03fabad39'
token_out = '0xc2132d05d31c914a87c6611c10748aeb04b58e8f'
amount_in = 1000

if __name__ == '__main__':
    get_quote(token_in, token_out, amount_in)