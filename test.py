import sys
import os
sys.path.append(os.path.dirname(__file__))

from app import app

if __name__ == "__main__":
    try:
        print("Testing app import...")
        print("App imported successfully!")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()