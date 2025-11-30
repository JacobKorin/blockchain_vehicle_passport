from time import time
import json
import hashlib
from collections import defaultdict


class Transaction:
    """
    Represents a vehicle passport transaction.
    Types: VEHICLE_CREATED, MILEAGE_UPDATE, SERVICE_RECORD, ACCIDENT_RECORD, OWNERSHIP_TRANSFER
    
    This is primarily a data object. Signing is handled using functions from other modules
    """
    
    def __init__(self, vin, tx_type, actor_id, role, payload):
        self.vin = vin
        self.type = tx_type
        self.actor_id = actor_id
        self.role = role
        self.timestamp = time()
        self.payload = payload
        self.tx_id = None
        self.signature = None
        
        # Compute transaction ID
        self.tx_id = self._compute_tx_id()
    
    def to_dict(self):
        #Convert transaction to dictionary
        return {
            'tx_id': self.tx_id,
            'vin': self.vin,
            'type': self.type,
            'actor_id': self.actor_id,
            'role': self.role,
            'timestamp': self.timestamp,
            'payload': self.payload,
            'signature': self.signature
        }
    
    #Compute SHA256 hash of transaction data (without signature)
    def _compute_tx_id(self):
        tx_data = {
            'vin': self.vin,
            'type': self.type,
            'actor_id': self.actor_id,
            'role': self.role,
            'timestamp': self.timestamp,
            'payload': self.payload
        }
        tx_string = json.dumps(tx_data, sort_keys=True).encode('utf8')
        h = hashlib.sha256()
        h.update(tx_string)
        return h.hexdigest()
    
    #Create transaction object from dictionary
    @classmethod
    def from_dict(cls, tx_dict):
        
        tx = cls(
            vin=tx_dict['vin'],
            tx_type=tx_dict['type'],
            actor_id=tx_dict['actor_id'],
            role=tx_dict['role'],
            payload=tx_dict['payload']
        )
        tx.timestamp = tx_dict['timestamp']
        tx.tx_id = tx_dict.get('tx_id')
        tx.signature = tx_dict.get('signature')
        return tx


#class representing a block in the blockchain
class Block:
    
    def __init__(self, block_number, transactions, previous_hash, nonce=0):
        self.block_number = block_number
        self.timestamp = time()
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = None
    
    def compute_hash(self):

        block_dict = {
            'block_number': self.block_number,
            'timestamp': self.timestamp,
            'transactions': [tx.to_dict() for tx in self.transactions],
            'nonce': self.nonce,
            'previous_hash': self.previous_hash
        }
        block_string = json.dumps(block_dict, sort_keys=True).encode('utf8')
        h = hashlib.sha256()
        h.update(block_string)
        return h.hexdigest()
    
    def to_dict(self):
        return {
            'block_number': self.block_number,
            'timestamp': self.timestamp,
            'transactions': [tx.to_dict() for tx in self.transactions],
            'nonce': self.nonce,
            'previous_hash': self.previous_hash,
            'hash': self.hash
        }


"""
Vehicle Passport Blockchain
Manages the chain of blocks and transaction validation
Includes VIN indexing for fast vehicle history lookups
"""
class Blockchain:
    
    
    def __init__(self):
        self.chain = []
        self.transactions = []
        
        # VIN Index: dict mapping VIN -> list of transactions
        self.vin_index = defaultdict(list)
        
        # Create genesis block
        self.create_block(nonce=0, previous_hash='00')
    
    #Add a block of transactions to the blockchain
    def create_block(self, nonce, previous_hash):
    
        block = Block(
            block_number=len(self.chain) + 1,
            transactions=self.transactions,
            previous_hash=previous_hash,
            nonce=nonce
        )
        
        block.hash = block.compute_hash()
        
        self._index_block(block)
        
        self.transactions = []
        
        self.chain.append(block)
        
        return block
    
    def add_transaction(self, transaction):
        self.transactions.append(transaction)
        return len(self.chain) + 1
    
    def get_last_block(self):
        return self.chain[-1]
    
    #checks if the blockchain is valid
    #1. Block hashes are correct
    #2. Block links are correct (previous_hash matches)
    def is_chain_valid(self):
    
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            
            if current_block.hash != current_block.compute_hash():
                print(f"Block {i} hash is invalid")
                return False
            
            if current_block.previous_hash != previous_block.hash:
                print(f"Block {i} previous_hash doesn't match")
                return False
        
        return True
    
    def get_chain_data(self):
        return [block.to_dict() for block in self.chain]
    
    # VIN indexing methods
    
    def _index_transaction(self, transaction):
      
        self.vin_index[transaction.vin].append(transaction)
    
    def _index_block(self, block):
    
        for transaction in block.transactions:
            self._index_transaction(transaction)
    
    def get_vehicle_history(self, vin):

        transactions = self.vin_index.get(vin, [])
        return sorted(transactions, key=lambda tx: tx.timestamp)
    
    def get_vehicle_info(self, vin):
        
        history = self.get_vehicle_history(vin)
        
        if not history:
            return None
        
        info = {
            'vin': vin,
            'make': None,
            'model': None,
            'year': None,
            'current_owner': None,
            'latest_mileage': None,
            'created_by': None,
            'created_at': None,
            'total_transactions': len(history)
        }
        
        # Extract information from transaction history
        for tx in history:
            if tx.type == 'VEHICLE_CREATED':
                info['make'] = tx.payload.get('make')
                info['model'] = tx.payload.get('model')
                info['year'] = tx.payload.get('year')
                info['latest_mileage'] = tx.payload.get('initial_mileage')
                info['current_owner'] = tx.payload.get('owner_id', tx.actor_id)
                info['created_by'] = tx.actor_id
                info['created_at'] = tx.timestamp
            
            elif tx.type == 'MILEAGE_UPDATE':
                info['latest_mileage'] = tx.payload.get('new_mileage')
            
            elif tx.type == 'OWNERSHIP_TRANSFER':
                info['current_owner'] = tx.payload.get('new_owner_id')
        
        return info
    
    def get_latest_mileage(self, vin):
        
        history = self.get_vehicle_history(vin)
        
        mileage = None
        
        for tx in history:
            if tx.type == 'VEHICLE_CREATED' and 'initial_mileage' in tx.payload:
                mileage = tx.payload['initial_mileage']
            elif tx.type == 'MILEAGE_UPDATE' and 'new_mileage' in tx.payload:
                mileage = tx.payload['new_mileage']
        
        return mileage
    
    def vehicle_exists(self, vin):
        
        return vin in self.vin_index and len(self.vin_index[vin]) > 0
    
    def rebuild_index_from_chain(self):
        self.vin_index = defaultdict(list)
        
        for block in self.chain:
            self._index_block(block)
        
        return len(self.vin_index)