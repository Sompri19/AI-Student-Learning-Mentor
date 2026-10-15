"""
Database connection module for AI Student Learning Mentor.
Manages PyMySQL connections, health status checks, and schema initialization.
"""
from contextlib import contextmanager
import logging
import os
import pymysql
from pymysql.cursors import DictCursor
from config import Config

logger = logging.getLogger(__name__)

# Expected tables for Phase 1 architecture verification
REQUIRED_TABLES = [
    'users',
    'student_profiles',
    'subjects',
    'topics',
    'resources',
    'study_plans',
    'study_plan_items',
    'quizzes',
    'quiz_attempts',
    'quiz_attempt_answers',
    'progress',
    'ai_chats'
]

# Reference-data scripts applied after the schema during initialisation, in order.
# Each is idempotent (INSERT IGNORE), so initialising an existing database is safe.
# Applications:
#   seed_quizzes.sql -> 115 practice questions across the 23 seeded topics
SEED_SQL_FILES = [
    'seed_quizzes.sql',
]


def _split_sql_statements(sql_content: str) -> list:
    """
    Splits a SQL script into executable statements, ignoring comment and blank lines.
    Statements are accumulated until a line terminates with a semicolon.
    """
    statements = []
    current = []
    for line in sql_content.splitlines():
        stripped = line.strip()
        if stripped.startswith('--') or not stripped:
            continue
        current.append(line)
        if stripped.endswith(';'):
            statements.append('\n'.join(current))
            current = []
    return statements


def _apply_sql_script(cursor, sql_path: str) -> None:
    """Executes every statement in a SQL script against the given cursor."""
    with open(sql_path, 'r', encoding='utf-8') as script_file:
        for statement in _split_sql_statements(script_file.read()):
            statement = statement.strip()
            if statement:
                cursor.execute(statement)


def sanitize_db_error(error: Exception) -> str:
    """
    Sanitize database error messages to guarantee no credentials or sensitive
    server details are exposed to client callers.
    """
    err_str = str(error)
    # Never expose configured password even if found in exception message
    if Config.DB_PASSWORD and Config.DB_PASSWORD in err_str:
        err_str = err_str.replace(Config.DB_PASSWORD, '******')
    
    # Generic, safe summary of common MySQL error codes
    if isinstance(error, pymysql.OperationalError):
        code, msg = error.args if len(error.args) == 2 else (0, str(error))
        if code == 2003:
            return "Unable to connect to MySQL server. Ensure MySQL is running in XAMPP."
        elif code == 1045:
            return "Access denied for database user. Verify DB_USER and DB_PASSWORD configuration."
        elif code == 1049:
            return f"Database '{Config.DB_NAME}' does not exist. Initialize schema first."
        return f"Database operational error (code {code}): {msg}"
    
    return "Database operation encountered an unexpected error."


def get_db_connection(database: str = None, autocommit: bool = True):
    """
    Creates and returns a new PyMySQL connection.
    
    Args:
        database: Optional database name. If None, uses Config.DB_NAME.
                  Pass empty string or False if connecting to server only.
        autocommit: Whether connection should autocommit transactions.
    
    Returns:
        pymysql.Connection: Active database connection.
    """
    db_to_use = Config.DB_NAME if database is None else (database or None)
    
    return pymysql.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=db_to_use,
        charset='utf8mb4',
        cursorclass=DictCursor,
        autocommit=autocommit,
        connect_timeout=5,
        ssl_ca=Config.DB_SSL_CA,
        ssl_verify_cert=True,
        ssl_verify_identity=True
    )


@contextmanager
def get_db_cursor(database: str = None, autocommit: bool = True):
    """
    Context manager that yields a cursor and safely closes connection afterwards.
    
    Example:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
    """
    connection = None
    try:
        connection = get_db_connection(database=database, autocommit=autocommit)
        with connection.cursor() as cursor:
            yield cursor
    finally:
        if connection and connection.open:
            connection.close()


def check_db_health() -> dict:
    """
    Checks the connectivity to MySQL and verifies the status of student_learning_mentor.
    Guarantees no passwords or credentials are exposed in the result.
    
    Returns:
        dict: Health status payload.
    """
    health = {
        "connected": False,
        "database_exists": False,
        "database_name": Config.DB_NAME,
        "tables_found": [],
        "all_required_tables_present": False,
        "error": None
    }
    
    connection = None
    try:
        # First test server connectivity without selecting a database
        connection = pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            charset='utf8mb4',
            cursorclass=DictCursor,
            connect_timeout=3,
            ssl_ca=Config.DB_SSL_CA,
            ssl_verify_cert=True,
            ssl_verify_identity=True
        )
        health["connected"] = True
        
        with connection.cursor() as cursor:
            # Check if database exists
            cursor.execute(
                "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = %s",
                (Config.DB_NAME,)
            )
            db_row = cursor.fetchone()
            if db_row:
                health["database_exists"] = True
                
                # Check required tables
                cursor.execute(
                    """
                    SELECT TABLE_NAME 
                    FROM INFORMATION_SCHEMA.TABLES 
                    WHERE TABLE_SCHEMA = %s AND TABLE_TYPE = 'BASE TABLE'
                    """,
                    (Config.DB_NAME,)
                )
                tables = [row["TABLE_NAME"] for row in cursor.fetchall()]
                health["tables_found"] = tables
                
                missing = [t for t in REQUIRED_TABLES if t not in tables]
                health["all_required_tables_present"] = (len(missing) == 0)
                if missing:
                    health["missing_tables"] = missing
            else:
                health["error"] = f"Database '{Config.DB_NAME}' does not exist."
                
    except Exception as exc:
        health["connected"] = False
        health["error"] = sanitize_db_error(exc)
        logger.warning("Database health check failed: %s", health["error"])
    finally:
        if connection and connection.open:
            connection.close()
            
    return health


def initialize_database(schema_path: str = None) -> tuple[bool, str]:
    """
    Applies the schema.sql script to create the database and tables, then applies
    the reference-data scripts listed in SEED_SQL_FILES (e.g. the quiz question bank).
    
    Args:
        schema_path: Optional path to schema.sql. Defaults to database/schema.sql.
        
    Returns:
        tuple[bool, str]: (Success status, description or error message)
    """
    if schema_path is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        schema_path = os.path.join(base_dir, 'database', 'schema.sql')
        
    if not os.path.isfile(schema_path):
        return False, f"Schema file not found at {schema_path}"
        
    with open(schema_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    connection = None
    try:
        # Connect to MySQL server without selecting database
        connection = pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            charset='utf8mb4',
            autocommit=True,
            connect_timeout=5,
            ssl_ca=Config.DB_SSL_CA,
            ssl_verify_cert=True,
            ssl_verify_identity=True
        )
        
        with connection.cursor() as cursor:
            # Execute statements by splitting semicolon (ignoring comments)
            for statement in _split_sql_statements(sql_content):
                statement = statement.strip()
                if statement:
                    cursor.execute(statement)
                    
                    
            # Apply reference-data scripts (idempotent) after the schema exists
            for seed_name in SEED_SQL_FILES:
                seed_path = os.path.join(os.path.dirname(schema_path), seed_name)
                if os.path.isfile(seed_path):
                    _apply_sql_script(cursor, seed_path)

        return True, "Database and tables initialized successfully."
    except Exception as exc:
        sanitized = sanitize_db_error(exc)
        return False, sanitized
    finally:
        if connection and connection.open:
            connection.close()
