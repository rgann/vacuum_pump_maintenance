"""
Script to test the Supabase connection
"""
import os
import sys
import logging
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Log to console
        logging.FileHandler('supabase_test.log')  # Log to file
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Import Supabase configuration
from supabase_config import (
    get_db_connection_string,
    test_db_connection,
    get_supabase_client,
    test_supabase_api,
    SUPABASE_URL,
    SUPABASE_KEY,
    SUPABASE_DB_HOST,
    SUPABASE_DB_NAME,
    SUPABASE_DB_USER,
    SUPABASE_DB_PORT
)

def check_environment_variables():
    """Check if all required environment variables are set"""
    # Check each variable individually to provide more detailed feedback
    env_vars = {
        "SUPABASE_URL": os.getenv("SUPABASE_URL"),
        "SUPABASE_KEY": os.getenv("SUPABASE_KEY"),
        "SUPABASE_DB_HOST": os.getenv("SUPABASE_DB_HOST"),
        "SUPABASE_DB_NAME": os.getenv("SUPABASE_DB_NAME"),
        "SUPABASE_DB_USER": os.getenv("SUPABASE_DB_USER"),
        "SUPABASE_DB_PASSWORD": os.getenv("SUPABASE_DB_PASSWORD"),
        "SUPABASE_DB_PORT": os.getenv("SUPABASE_DB_PORT")
    }

    # Log all variables (except password)
    for var, value in env_vars.items():
        if var == "SUPABASE_DB_PASSWORD":
            logger.info(f"{var}: {'SET' if value else 'NOT SET'}")
        else:
            logger.info(f"{var}: {value if value else 'NOT SET'}")

    # Check required variables
    required_vars = {
        "SUPABASE_URL": env_vars["SUPABASE_URL"],
        "SUPABASE_KEY": env_vars["SUPABASE_KEY"],
        "SUPABASE_DB_HOST": env_vars["SUPABASE_DB_HOST"],
        "SUPABASE_DB_PASSWORD": env_vars["SUPABASE_DB_PASSWORD"]
    }

    missing_vars = [var for var, value in required_vars.items() if not value]

    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        return False

    # Check port specifically
    port_str = env_vars["SUPABASE_DB_PORT"]
    if port_str:
        try:
            port = int(port_str)
            logger.info(f"SUPABASE_DB_PORT parsed as integer: {port}")
        except ValueError:
            logger.error(f"SUPABASE_DB_PORT is not a valid integer: '{port_str}'")
            return False
    else:
        logger.info("SUPABASE_DB_PORT not set, will use default (5432)")

    logger.info("All required environment variables are set")
    return True

def print_connection_info():
    """Print connection information"""
    # Mask sensitive information
    masked_key = f"{SUPABASE_KEY[:5]}...{SUPABASE_KEY[-5:]}" if SUPABASE_KEY else "Not set"
    masked_password = "********" if os.getenv("SUPABASE_DB_PASSWORD") else "Not set"

    logger.info("Supabase Connection Information:")
    logger.info(f"  SUPABASE_URL: {SUPABASE_URL}")
    logger.info(f"  SUPABASE_KEY: {masked_key}")
    logger.info(f"  SUPABASE_DB_HOST: {SUPABASE_DB_HOST}")
    logger.info(f"  SUPABASE_DB_NAME: {SUPABASE_DB_NAME}")
    logger.info(f"  SUPABASE_DB_USER: {SUPABASE_DB_USER}")
    logger.info(f"  SUPABASE_DB_PORT: {SUPABASE_DB_PORT}")
    logger.info(f"  SUPABASE_DB_PASSWORD: {masked_password}")

def test_sqlalchemy_connection():
    """Test SQLAlchemy connection to Supabase"""
    try:
        # Get connection string
        connection_string = get_db_connection_string()
        if not connection_string:
            logger.error("Failed to get database connection string")
            return False

        # Test connection
        import sqlalchemy
        from sqlalchemy import text

        logger.info(f"Creating SQLAlchemy engine with connection string: {connection_string.replace(os.getenv('SUPABASE_DB_PASSWORD', ''), '****')}")
        engine = sqlalchemy.create_engine(connection_string)

        logger.info("Connecting to database...")
        with engine.connect() as connection:
            # Try to execute a simple query
            logger.info("Executing SELECT 1 query...")
            result = connection.execute(text("SELECT 1")).scalar()
            logger.info(f"SQLAlchemy connection test result: {result}")

            # Try to get database version
            logger.info("Executing SELECT version() query...")
            version = connection.execute(text("SELECT version()")).scalar()
            logger.info(f"Database version: {version}")

            return True
    except Exception as e:
        logger.error(f"Error testing SQLAlchemy connection: {e}")
        return False

if __name__ == "__main__":
    try:
        logger.info("Testing Supabase connection...")

        # Check environment variables
        if not check_environment_variables():
            sys.exit(1)

        # Print connection information
        print_connection_info()

        # Test database connection
        logger.info("Testing database connection...")
        if not test_db_connection():
            logger.error("Failed to connect to Supabase database")
            sys.exit(1)

        logger.info("Database connection successful")

        # Test Supabase API
        logger.info("Testing Supabase API...")
        api_result = test_supabase_api()
        if not api_result:
            logger.error("Failed to connect to Supabase API")
            sys.exit(1)

        logger.info("Supabase API connection successful - Note: A 404 error is expected and indicates success")

        # Test SQLAlchemy connection
        logger.info("Testing SQLAlchemy connection...")
        if not test_sqlalchemy_connection():
            logger.error("Failed to connect to Supabase using SQLAlchemy")
            sys.exit(1)

        logger.info("SQLAlchemy connection successful")

        logger.info("All Supabase connection tests passed!")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error during Supabase connection test: {e}")
        sys.exit(1)
