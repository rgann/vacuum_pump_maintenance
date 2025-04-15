import os
from setup import setup_database

if __name__ == "__main__":
    print("Initializing database with sample data...")

    # Print the current directory for debugging
    current_dir = os.path.abspath(os.path.dirname(__file__))
    print(f"Current directory: {current_dir}")
    print(f"Database will be created in the current directory")

    setup_database()
    print("Done!")
