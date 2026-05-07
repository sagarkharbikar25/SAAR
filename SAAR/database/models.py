# database/models.py

TABLES = [

    # -----------------------------
    # USER IDENTITY (SAFE)
    # -----------------------------
    """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        language TEXT,
        face_embedding TEXT,      -- numeric vector, NOT image
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """,

    # -----------------------------
    # LONG-TERM MEMORY (CORE)
    # -----------------------------
    """
    CREATE TABLE IF NOT EXISTS memory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        type TEXT,                -- fact | preference | relation | skill
        key TEXT,
        value TEXT,
        importance INTEGER,       -- 1 to 10
        confidence REAL,          -- 0.0 to 1.0
        last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """,

    # -----------------------------
    # BEHAVIOR / HABITS
    # -----------------------------
    """
    CREATE TABLE IF NOT EXISTS behavior (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        action TEXT,              -- shutdown, open_app, code
        context TEXT,             -- night, morning, stressed
        count INTEGER DEFAULT 1,
        last_seen DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """,

    # -----------------------------
    # COMMAND HISTORY
    # -----------------------------
    """
    CREATE TABLE IF NOT EXISTS commands (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        command_text TEXT,
        intent TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """,

    # -----------------------------
    # CHAT LOG (OPTIONAL, LONG-TERM)
    # -----------------------------
    """
    CREATE TABLE IF NOT EXISTS chat (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        role TEXT,                -- user / assistant
        text TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """,

    # -----------------------------
    # SESSION MEMORY (TEMPORARY)
    # -----------------------------
    """
    CREATE TABLE IF NOT EXISTS session_memory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """,

    # -----------------------------
    # MOOD HISTORY (PHASE 5)
    # -----------------------------
    """
    CREATE TABLE IF NOT EXISTS mood_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        polarity REAL,
        label TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """
]
