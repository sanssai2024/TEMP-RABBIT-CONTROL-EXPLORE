import os

# Browser tests explicitly use isolated SQLite; runtime configuration remains MySQL-oriented.
os.environ["DATABASE_URL"] = "sqlite:///./temp_rabbit_test_app.db"
