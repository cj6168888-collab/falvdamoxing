import sys
sys.path.insert(0, 'd:/www/法律大模型')

print("Testing database functions...")

# Test get_loans
from app.db.storage import get_loans, get_contracts, init_database

# Initialize database
init_database()

print("\nTesting get_loans()...")
try:
    loans = get_loans()
    print(f"Success! Found {len(loans)} loans")
except Exception as e:
    print(f"Error in get_loans: {e}")
    import traceback
    traceback.print_exc()

print("\nTesting get_contracts()...")
try:
    contracts = get_contracts()
    print(f"Success! Found {len(contracts)} contracts")
except Exception as e:
    print(f"Error in get_contracts: {e}")
    import traceback
    traceback.print_exc()

print("\nDone!")