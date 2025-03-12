import json
from web3 import Web3

# Connect to a local Ethereum node
w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))

# Load the contract ABI
with open('../build/contracts/Certification.json') as f:
    contract_json = json.load(f)
    contract_abi = contract_json['abi']

# Set the contract address (update this with the deployed contract address)
contract_address = '0xCbf8e871A97d3819b3F24263f6148C83A51025F5'

# Create the contract instance
contract = w3.eth.contract(address=contract_address, abi=contract_abi)
