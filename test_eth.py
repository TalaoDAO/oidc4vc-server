
from web3.auto import w3
from eth_keys import keys


private_key = '0x24b3ce314686773ba97b42f6d900be8786caf3dbd9690fc4a920f91c1c240b4f'

from eth_keys import keys
from eth_utils import decode_hex

priv_key_bytes = decode_hex(private_key)
priv_key = keys.PrivateKey(priv_key_bytes)
pub_key = priv_key.public_key

print(pub_key)
print(pub_key.to_checksum_address())
