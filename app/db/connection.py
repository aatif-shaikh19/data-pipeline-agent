import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any, Optional
from urllib.parse import unquote
from app.core.config import settings
from app.core.logging import logger

_connection_pool: Optional[pool.SimpleConnectionPool] = None


def get_connection_params(dsn: Optional[str] = None) -> Dict[str, Any]:
    """
    Parse a PostgreSQL connection URL into safe connection keyword arguments.
    Gracefully handles unescaped special characters like '@' in passwords.
    """
    url = dsn or settings.DATABASE_URL
    if not url:
        return {}

    if "://" in url:
        url = url.split("://", 1)[1]

    # Handle query parameters (e.g., ?sslmode=require)
    query_params: Dict[str, str] = {}
    if "?" in url:
        url, query_str = url.split("?", 1)
        for part in query_str.split("&"):
            if "=" in part:
                k, v = part.split("=", 1)
                query_params[k] = v

    # Host is always after the LAST '@'
    if "@" in url:
        auth_part, host_part = url.rsplit("@", 1)
        if ":" in auth_part:
            user, password = auth_part.split(":", 1)
        else:
            user, password = auth_part, ""
    else:
        auth_part = ""
        user, password = "", ""
        host_part = url

    # Database name is after '/'
    if "/" in host_part:
        host_port, dbname = host_part.split("/", 1)
    else:
        host_port, dbname = host_part, "postgres"

    # Port is after ':' in host_port
    if ":" in host_port:
        host, port_str = host_port.split(":", 1)
        try:
            port = int(port_str)
        except ValueError:
            port = 5432
    else:
        host = host_port
        port = 5432

    # Auto-enable SSL for Supabase if not specified
    sslmode = query_params.get("sslmode")
    if not sslmode and ("supabase.co" in host or "pooler.supabase.com" in host):
        sslmode = "require"

    params: Dict[str, Any] = {
        "user": unquote(user),
        "password": unquote(password),
        "host": host,
        "port": port,
        "database": dbname,
    }
    if sslmode:
        params["sslmode"] = sslmode

    return params


def get_db_pool() -> Optional[pool.SimpleConnectionPool]:
    """Initialize or retrieve the PostgreSQL connection pool."""
    global _connection_pool
    if _connection_pool is None and settings.DATABASE_URL:
        params = get_connection_params()
        try:
            _connection_pool = pool.SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                **params
            )
            logger.info("PostgreSQL connection pool initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL pool: {e}")
            raise e
    return _connection_pool


def execute_readonly_query(
    query: str, params: Optional[tuple] = None
) -> List[Dict[str, Any]]:
    """
    Execute a parameterized read-only query using the connection pool.
    Returns results as a list of dictionaries.
    """
    db_pool = get_db_pool()
    if not db_pool:
        logger.warning("No active database pool available. Returning empty result.")
        return []

    conn = None
    try:
        conn = db_pool.getconn()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params or ())
            results = cursor.fetchall()
            return [dict(row) for row in results]
    except Exception as e:
        logger.error(f"Database query error: {e}", exc_info=True)
        raise e
    finally:
        if conn and db_pool:
            db_pool.putconn(conn)
