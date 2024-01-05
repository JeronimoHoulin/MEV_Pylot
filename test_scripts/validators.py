from web3 import Web3
from decimal import Decimal


#Missing uncle and Nephwe rewards
#https://docs.alchemy.com/docs/how-to-calculate-ethereum-miner-rewards

#The London fork introduced maxFeePerGas and maxPriorityFeePerGas transaction parameters which should be used over gasPrice whenever possible.
#https://web3py.readthedocs.io/en/v5/gas_price.html

infura_key = '7e452892f2204d6a90e814c4a03a7b1d'
w3 = Web3(Web3.HTTPProvider(f'https://mainnet.infura.io/v3/{infura_key}'))


validator_adrs = '0x4838B106FCe9647Bdf1E7877BF73cE8B0BAD5f97'


block_intel = w3.eth.get_block(18216877) #'latest'
burnt_fees = w3.fromWei(block_intel.gasUsed * block_intel.baseFeePerGas, 'ether')

miner = block_intel.miner



latest_height = block_intel.number

"""
print()
print("Last 5 block Validators: ")
for i in range(latest_height-5, latest_height):
    block = w3.eth.get_block(i)
    print(block.miner)
    print()
"""

latest_block_txns = block_intel.transactions
for i in latest_block_txns:
    txn_intel = w3.eth.get_transaction(i)
    rewards = 0
    rewards += (txn_intel.gas * txn_intel.gasPrice)


def convert(amount):
    #: Convert gwei to wei
    wei_amount = Decimal(amount) * (Decimal(10) ** 9)  # Gigaweis are billions
    eth_amount = w3.fromWei(wei_amount,'ether')
    return eth_amount

rewards = convert(rewards)

print()
print("Rewards: " + str(rewards))
print("   Minus Burnt fees: " + str(burnt_fees) + ":")
print("")
print("Total Rewards: " + str(rewards - Decimal(burnt_fees)))
print("Sent to validator: " + miner)