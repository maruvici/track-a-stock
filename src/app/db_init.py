def init_db(db):
    # Check for existing tables
    add_history_exist = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='addHistory';"
    )
    history_exist = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='history';"
    )
    shares_exist = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='shares';"
    )

    if not history_exist:
        db.execute("""
            CREATE TABLE history (
                id INTEGER NOT NULL,
                transactType TEXT NOT NULL,
                stockSymbol TEXT NOT NULL,
                stockPrice NUMERIC NOT NULL,
                shares INTEGER NOT NULL,
                timestamp DATETIME NOT NULL,
                FOREIGN KEY (id) REFERENCES users(id)
            );
        """)

    if not shares_exist:
        db.execute("""
            CREATE TABLE shares (
                id INTEGER NOT NULL,
                stockSymbol TEXT NOT NULL,
                stockShares INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (id) REFERENCES users(id)
            );
        """)

    if not add_history_exist:
        db.execute("""
            CREATE TABLE addHistory (
                id INTEGER NOT NULL,
                cash NUMERIC NOT NULL,
                timestamp DATETIME NOT NULL,
                FOREIGN KEY (id) REFERENCES users(id)
            );
        """)
