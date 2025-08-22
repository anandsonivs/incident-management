import inspect as py_inspect
from sqlalchemy import inspect
from sqlalchemy.orm import class_mapper

from app.db.base import Base
from app.db.session import engine

# Import all models to register them with SQLAlchemy
from app.models import *

def list_models():
    # Get all model classes that inherit from Base
    models = []
    
    # Import the models module to get access to all models
    import app.models
    
    for name, obj in py_inspect.getmembers(app.models):
        if (py_inspect.isclass(obj) and 
            issubclass(obj, Base) and 
            obj != Base and 
            hasattr(obj, '__tablename__')):
            models.append(obj)
    
    print(f"Found {len(models)} models:")
    for model in models:
        print(f"- {model.__name__} (table: {model.__tablename__})")
    
    # Check if tables exist in the database
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"\nTables in database ({len(tables)}):")
        for table in tables:
            print(f"- {table}")
            
        # Check if we can map the models to tables
        print("\nModel to table mapping:")
        for model in models:
            try:
                mapper = class_mapper(model)
                print(f"- {model.__name__} -> {mapper.persist_selectable.name}")
            except Exception as e:
                print(f"- {model.__name__}: Error - {str(e)}")
                
    except Exception as e:
        print(f"\nError inspecting database: {str(e)}")
        print("Make sure the database is running and accessible.")

if __name__ == "__main__":
    list_models()
