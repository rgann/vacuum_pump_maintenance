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

# Handle port with explicit error checking
try:
    port_str = os.getenv("SUPABASE_DB_PORT", "5432")
    if not port_str or port_str.strip() == "":
        logger.warning("SUPABASE_DB_PORT is empty, using default port 5432")
        SUPABASE_DB_PORT = 5432
    else:
        SUPABASE_DB_PORT = int(port_str)
        logger.info(f"Using database port: {SUPABASE_DB_PORT}")
except ValueError as e:
    logger.warning(f"Invalid SUPABASE_DB_PORT value: {port_str}. Using default port 5432")
    SUPABASE_DB_PORT = 5432

# Database connection string for SQLAlchemy
def get_db_connection_string():
    """Get the database connection string for SQLAlchemy"""
    # Check for required credentials
    missing_vars = []
    if not SUPABASE_DB_HOST:
        missing_vars.append("SUPABASE_DB_HOST")
    if not SUPABASE_DB_PASSWORD:
        missing_vars.append("SUPABASE_DB_PASSWORD")

    if missing_vars:
        logger.warning(f"Missing required Supabase database credentials: {', '.join(missing_vars)}")
        return None

    # Extract just the hostname if a full connection string was provided
    host = SUPABASE_DB_HOST
    if '://' in host:
        # This looks like a full connection string, not just a hostname
        logger.warning(f"SUPABASE_DB_HOST appears to be a full connection string. Attempting to extract hostname.")
        try:
            # Try to extract just the hostname part
            if '@' in host:
                # Format like: postgresql://user:pass@hostname:port/dbname
                host = host.split('@')[1].split(':')[0]
            else:
                # Format like: hostname:port/dbname
                host = host.split(':')[0]

            logger.info(f"Extracted hostname from connection string: {host}")
        except Exception as e:
            logger.error(f"Failed to extract hostname from connection string: {e}")
            return None

    # Log all connection parameters (except password)
    logger.info(f"Database connection parameters:")
    logger.info(f"  Host: {host}")
    logger.info(f"  Database: {SUPABASE_DB_NAME}")
    logger.info(f"  User: {SUPABASE_DB_USER}")
    logger.info(f"  Port: {SUPABASE_DB_PORT}")

    # Build and return the connection string
    connection_string = f"postgresql://{SUPABASE_DB_USER}:{SUPABASE_DB_PASSWORD}@{host}:{SUPABASE_DB_PORT}/{SUPABASE_DB_NAME}"

    # Log a masked version of the connection string
    masked_connection = connection_string.replace(SUPABASE_DB_PASSWORD, "****")
    logger.info(f"Connection string: {masked_connection}")

    return connection_string

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
    from sqlalchemy import text

    connection_string = get_db_connection_string()
    if not connection_string:
        return False

    try:
        engine = sqlalchemy.create_engine(connection_string)
        with engine.connect() as connection:
            # Use SQLAlchemy text() to create a proper SQL expression
            result = connection.execute(text("SELECT 1")).scalar()
            logger.info(f"Database connection test result: {result}")
            return result == 1
    except Exception as e:
        logger.error(f"Error testing database connection: {e}")
        return False

# Test Supabase API connection
def test_supabase_api():
    """Test the Supabase API connection"""
    client = get_supabase_client()
    if not client:
        logger.error("Failed to create Supabase client")
        return False

    try:
        # Try to get the Supabase server health
        # This is a more reliable way to test the connection
        client.table("_dummy").select("*").limit(1).execute()
        logger.info("Supabase API connection successful")
        return True
    except Exception as e:
        # Check if it's a 404 error or relation doesn't exist error, which is expected
        error_str = str(e).lower()
        if ("404" in error_str or
            "not found" in error_str or
            "does not exist" in error_str or
            "42p01" in error_str):  # PostgreSQL error code for undefined table
            logger.info(f"Supabase API connection successful (expected error: {e})")
            return True
        else:
            logger.error(f"Error testing Supabase API connection: {e}")
            return False
