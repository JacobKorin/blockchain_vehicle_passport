import unittest
import json
from blockchain import Blockchain, Transaction, Block

class TestBlockchainLogic(unittest.TestCase):

    def setUp(self):
        self.bc = Blockchain()

    #confirm genesis block is created correctly    
    def test_genesis_block(self):
        self.assertEqual(len(self.bc.chain), 1)
        self.assertEqual(self.bc.chain[0].previous_hash, '00')

    def test_transaction_creation(self):
        # test transaction
        tx = Transaction(
            vin="TEST-VIN", 
            tx_type="VEHICLE_CREATED", 
            actor_id="user1", 
            role="MANUFACTURER", 
            payload={"year": 2022}
        )
        self.assertIsNotNone(tx.tx_id)
        self.assertEqual(tx.vin, "TEST-VIN")

    #testing instant mining
    def test_block_mining(self):
        
        # Create a dummy transaction
        tx = Transaction("V1", "TEST", "u1", "role", {})
        
       
        self.bc.add_transaction(tx)
        self.assertEqual(len(self.bc.transactions), 1)
        
        #mine block
        last_hash = self.bc.get_last_block().hash
        self.bc.create_block(nonce=1, previous_hash=last_hash)
       
        self.assertEqual(len(self.bc.chain), 2)
        self.assertEqual(len(self.bc.transactions), 0) # Pool should be empty
        self.assertEqual(self.bc.chain[1].previous_hash, last_hash)

    def test_chain_validity(self):
        """Test the cryptographic integrity check"""
        # Add a valid block
        tx = Transaction("V1", "TEST", "u1", "role", {})
        self.bc.add_transaction(tx)
        self.bc.create_block(nonce=1, previous_hash=self.bc.get_last_block().hash)
        
        # Should be valid
        self.assertTrue(self.bc.is_chain_valid())
        
        # TAMPERING ATTACK!
        # Modify the data in the block
        self.bc.chain[1].transactions[0].vin = "HACKED-VIN"
        
        # Should now be invalid because hash won't match data
        self.assertFalse(self.bc.is_chain_valid())

if __name__ == '__main__':
    unittest.main(exit=False)
    input("Press Enter to close...")