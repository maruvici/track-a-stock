from flask import Flask
from flask_session import Session
from .config import Config
from cs50 import SQL
from .db_init import init_db
from .routes import main
from .helpers import usd 

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize session and database
    Session(app)
    app.db = SQL(app.config["DATABASE_URL"])
    init_db(app.db)

    # Register Jinja filters
    # Replace/Expand with other currencies as needed
    app.jinja_env.filters["usd"] = usd 

    # Register routes
    app.register_blueprint(main)

    return app
