"""
Cryptographic utilities for transaction signing and verification
Separates signing logic from Transaction data objects
"""

import binascii
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256
from Crypto.Random import new

# sign a transaction with a private key
# no return modifies in place
def sign_transaction(transaction, private_key_hex):
    if not transaction.tx_id:
        raise ValueError("Transaction must have tx_id before signing")
    
    private_key = RSA.importKey(binascii.unhexlify(private_key_hex))
    signer = PKCS1_v1_5.new(private_key)
    h = SHA256.new(transaction.tx_id.encode('utf8'))
    signature = binascii.hexlify(signer.sign(h)).decode('ascii')
    
    transaction.signature = signature


def verify_transaction_signature(transaction, public_key_hex):
    if not transaction.signature or not transaction.tx_id:
        return False
    
    try:
        public_key = RSA.importKey(binascii.unhexlify(public_key_hex))
        verifier = PKCS1_v1_5.new(public_key)
        h = SHA256.new(transaction.tx_id.encode('utf8'))
        return verifier.verify(h, binascii.unhexlify(transaction.signature))
    except (ValueError, TypeError):
        return False


def generate_keypair():

    random_gen = new().read
    private_key = RSA.generate(1024, random_gen)
    public_key = private_key.publickey()
    
    private_key_hex = binascii.hexlify(private_key.export_key(format='DER')).decode('ascii')
    public_key_hex = binascii.hexlify(public_key.export_key(format='DER')).decode('ascii')
    
    return private_key_hex, public_key_hex