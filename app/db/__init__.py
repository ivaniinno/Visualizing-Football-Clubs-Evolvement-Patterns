import psycopg2
import psycopg2.extras
from config import Config


def get_conn():
    """
    Creates a PostgreSQL database connection with read-only privileges.
    Uses RealDictCursor to return query results as key-value pairs instead of tuples.
    Caller is responsible for closing the connection.

    Returns:
        psycopg2.extensions.connection
    """
    return psycopg2.connect(
        database=Config.DB_NAME,
        user=Config.DB_READ_ONLY_USER,
        password=Config.DB_READ_ONLY_USER_PASSWORD,
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        cursor_factory=psycopg2.extras.RealDictCursor
    )
