import sys
import os

# Ensure current directory is in path
sys.path.append(os.getcwd())

try:
    from sqlalchemy import create_engine
    from models import Base
    
    # Create an in-memory SQLite database
    # This checks if the models are valid and can form a schema
    engine = create_engine('sqlite:///:memory:', echo=True)
    
    print("Attempting to create all tables...")
    Base.metadata.create_all(engine)
    print("SUCCESS: All tables created successfully!")
    
except Exception as e:
    print(f"FAILURE: An error occurred: {e}")
    sys.exit(1)
