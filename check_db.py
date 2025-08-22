import sys
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings

def check_database():
    settings = get_settings()
    print(f"Connecting to database: {settings.DATABASE_URL}")
    
    try:
        # Create engine
        engine = create_engine(settings.DATABASE_URL)
        
        # Test connection
        with engine.connect() as conn:
            print("✅ Successfully connected to the database")
            
            # List all tables
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            
            if not tables:
                print("\n❌ No tables found in the database")
            else:
                print(f"\n📋 Found {len(tables)} tables:")
                for table in tables:
                    print(f"- {table}")
                    
                    # List columns for each table
                    columns = inspector.get_columns(table)
                    for column in columns:
                        print(f"  - {column['name']}: {column['type']}")
                    print()
                    
    except Exception as e:
        print(f"\n❌ Error connecting to the database: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    check_database()
