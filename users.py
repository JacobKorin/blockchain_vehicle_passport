
'''
This module defines users, permissions
'''
from crypto_utils import generate_keypair, sign_transaction, verify_transaction_signature


class User:
    
    def __init__(self, user_id, role, private_key, public_key):
        self.user_id = user_id
        self.role = role
        self.private_key = private_key
        self.public_key = public_key
    
    def to_dict(self):
        return {
            'user_id': self.user_id,
            'role': self.role,
            'public_key': self.public_key
        }


# Role definitions and permissions
ROLES = {
    'MANUFACTURER': ['VEHICLE_CREATED', 'OWNERSHIP_TRANSFER'],
    'DMV': ['VEHICLE_CREATED', 'OWNERSHIP_TRANSFER'],
    'MECHANIC': ['MILEAGE_UPDATE', 'SERVICE_RECORD'],
    'INSURER': ['ACCIDENT_RECORD'],
    'BUYER': []  # Read-only
}


# Global user registry
USERS = {}


def initialize_users():
    global USERS
    
    user_configs = [
        # Manufacturers
        ('manufacturer_1', 'MANUFACTURER'),
        ('manufacturer_2', 'MANUFACTURER'),
        
        # DMV offices
        ('dmv_1', 'DMV'),
        ('dmv_2', 'DMV'),
        
        # Mechanics
        ('mechanic_1', 'MECHANIC'),
        ('mechanic_2', 'MECHANIC'),
        ('mechanic_3', 'MECHANIC'),
        
        # Insurers
        ('insurer_1', 'INSURER'),
        ('insurer_2', 'INSURER'),
        
        # Buyers/Owners
        ('buyer_1', 'BUYER'),
        ('buyer_2', 'BUYER'),
        ('buyer_3', 'BUYER'),
    ]
    
    for user_id, role in user_configs:
        private_key, public_key = generate_keypair()
        user = User(user_id, role, private_key, public_key)
        USERS[user_id] = user
    
    return USERS


def get_user(user_id):
    return USERS.get(user_id)


def get_users_by_role(role):
    return [user for user in USERS.values() if user.role == role]


def get_all_users():
    return USERS


def can_user_create_transaction(user_id, transaction_type):
    user = get_user(user_id)
    if not user:
        return False
    
    allowed_types = ROLES.get(user.role, [])
    return transaction_type in allowed_types


def create_and_sign_transaction(user_id, vin, tx_type, payload):
    from blockchain import Transaction
    
    user = get_user(user_id)
    if not user:
        raise ValueError(f"User {user_id} not found")
    
    # Check permissions
    if not can_user_create_transaction(user_id, tx_type):
        raise PermissionError(
            f"User {user_id} with role {user.role} cannot create {tx_type} transactions"
        )
    
    # Create transaction
    transaction = Transaction(
        vin=vin,
        tx_type=tx_type,
        actor_id=user_id,
        role=user.role,
        payload=payload
    )
    
    # Sign transaction
    sign_transaction(transaction, user.private_key)
    
    return transaction


def verify_transaction(transaction):
    # Get user
    user = get_user(transaction.actor_id)
    if not user:
        return False
    
    # Verify signature
    if not verify_transaction_signature(transaction, user.public_key):
        return False
    
    # Verify permissions
    if not can_user_create_transaction(transaction.actor_id, transaction.type):
        return False
    
    return True