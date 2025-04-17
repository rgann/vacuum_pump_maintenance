"""
Supabase configuration and utility functions
"""
import os
import logging
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_DB_HOST = os.getenv("SUPABASE_DB_HOST")
SUPABASE_DB_NAME = os.getenv("SUPABASE_DB_NAME", "postgres")
SUPABASE_DB_USER = os.getenv("SUPABASE_DB_USER", "postgres")
SUPABASE_DB_PASSWORD = os.getenv("SUPABASE_DB_PASSWORD")
SUPABASE_DB_PORT = os.getenv("SUPABASE_DB_PORT", "5432")

# Database connection string for SQLAlchemy
def get_db_connection_string():
    """Get the database connection string for SQLAlchemy"""
    if not all([SUPABASE_DB_HOST, SUPABASE_DB_PASSWORD]):
        logger.warning("Supabase database credentials not found in environment variables")
        return None
        
    return f"postgresql://{SUPABASE_DB_USER}:{SUPABASE_DB_PASSWORD}@{SUPABASE_DB_HOST}:{SUPABASE_DB_PORT}/{SUPABASE_DB_NAME}"

# Initialize Supabase client
def get_supabase_client() -> Client:
    """Get a Supabase client instance"""
    if not all([SUPABASE_URL, SUPABASE_KEY]):
        logger.warning("Supabase API credentials not found in environment variables")
        return None
        
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        logger.error(f"Error creating Supabase client: {e}")
        return None

# Test database connection
def test_db_connection():
    """Test the database connection"""
    import sqlalchemy
    
    connection_string = get_db_connection_string()
    if not connection_string:
        return False
        
    try:
        engine = sqlalchemy.create_engine(connection_string)
        with engine.connect() as connection:
            result = connection.execute("SELECT 1").scalar()
            return result == 1
    except Exception as e:
        logger.error(f"Error testing database connection: {e}")
        return False

# Test Supabase API connection
def test_supabase_api():
    """Test the Supabase API connection"""
    client = get_supabase_client()
    if not client:
        return False
        
    try:
        # Try to fetch the server timestamp
        response = client.table("_dummy").select("*").limit(1).execute()
        return True
    except Exception as e:
        logger.error(f"Error testing Supabase API connection: {e}")
        return False
