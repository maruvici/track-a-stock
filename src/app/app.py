import os
from datetime import datetime

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Create history and shares table if not yet created
addHistoryExist = db.execute(
    "SELECT name FROM sqlite_master WHERE type='table' AND name='addHistory';")
historyExist = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='history';")
sharesExist = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='shares';")

if not historyExist:
    db.execute("CREATE TABLE history (id INTEGER NOT NULL, transactType TEXT NOT NULL, stockSymbol TEXT NOT NULL, stockPrice NUMERIC NOT NULL, shares INTEGER NOT NULL, timestamp DATETIME NOT NULL, FOREIGN KEY (id) REFERENCES users(id));")
if not sharesExist:
    db.execute("CREATE TABLE shares (id INTEGER NOT NULL, stockSymbol TEXT NOT NULL, stockShares INTEGER NOT NULL DEFAULT 0, FOREIGN KEY (id) REFERENCES users(id));")
if not addHistoryExist:
    db.execute("CREATE TABLE addHistory (id INTEGER NOT NULL, cash NUMERIC NOT NULL, timestamp DATETIME NOT NULL, FOREIGN KEY (id) REFERENCES users(id));")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    total_sum = 0

    # Obtain all current stocks and shares of user
    stock_list = db.execute(
        "SELECT stockSymbol, stockShares FROM shares WHERE id = ?;", session["user_id"])

    # Iterate through each stock in user's stock list
    for stock in stock_list:
        # Obtain Stock Details
        stock_details = lookup(stock["stockSymbol"])

        # Validate Stock Symbol
        if stock_details == None:
            return apology("must provide valid stock symbol", 400)

        # Insert price in stock dict
        price = round(stock_details["price"], 2)
        stock["stockPrice"] = price

        # Insert total holdings value in stock dict
        total_holdings = price * stock["stockShares"]
        stock["stockTotalHoldings"] = round(total_holdings, 2)

        # Add total holdings to total sum
        total_sum += total_holdings

    # Obtain current cash balance of user
    user_cash = db.execute("SELECT cash FROM users WHERE id = ?;", session["user_id"])[0]["cash"]

    # Add current cash balanace to total sum
    total_sum += user_cash
    return render_template("index.html", stockList=stock_list, userCash=round(user_cash, 2), totalSum=round(total_sum, 2))


@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    """Add cash to user's cash balance"""

    if request.method == "POST":
        cash = int(request.form.get("cash"))

        if cash <= 0:
            return apology("must provide valid cash to add", 400)

        # Update user's cash balance
        db.execute("UPDATE users SET cash = cash + ? WHERE id = ?;", cash, session["user_id"])

        # Insert add transaction to addHistory table
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        db.execute("INSERT INTO addHistory (id, cash, timestamp) VALUES (?, ?, ?);",
                   session["user_id"], cash, timestamp)

        return redirect("/")
    else:
        return render_template("add.html")


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    if request.method == "POST":
        # Get Form and Session Details
        symbol = request.form.get("symbol").upper()
        try:
            shares = int(request.form.get("shares"))
        except ValueError:
            return apology("must provide valid share count", 400)
        user_id = session["user_id"]

        # Obtain Stock Details
        stock_details = lookup(symbol)

        # Validate Stock Symbol
        if stock_details == None:
            return apology("must provide valid stock symbol", 400)

        # Validate Shares
        if shares < 1:
            return apology("must provide valid share count", 400)

        # Determine cash balance of user
        user_cash = db.execute("SELECT cash FROM users WHERE id = ?;", user_id)[0]["cash"]

        # Validate user can buy stock
        price = stock_details["price"]
        if price * shares > user_cash:
            return apology("unable to buy with cash balance", 400)

        # Insert transaction details to transaction history table
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        db.execute("INSERT INTO history (id, transactType, stockSymbol, stockPrice, shares, timestamp) VALUES (?, ?, ?, ?, ?, ?);",
                   user_id, "BUY", symbol, price, shares, timestamp)

        # Check if stock already exists in shares table
        stockExist = db.execute(
            "SELECT * FROM shares WHERE stockSymbol = ? AND id = ?;", symbol, user_id)

        # Adjust user's shares in shares table
        if stockExist:
            db.execute(
                "UPDATE shares SET stockShares = stockShares + ? WHERE stockSymbol = ? AND id = ?;", shares, symbol, user_id)
        else:
            db.execute("INSERT INTO shares (id, stockSymbol, stockShares) VALUES (?, ?, ?);",
                       user_id, symbol, shares)

        # Adjust user's cash balance in users table
        db.execute("UPDATE users SET cash = cash - ? WHERE id = ?", price * shares, user_id)
        return redirect("/")

    else:
        return render_template("buy.html")


@app.route("/change", methods=["GET", "POST"])
def change():
    """Change a given user's password"""

    if request.method == "POST":
        # Get Form Details
        username = request.form.get("username")
        old_password = request.form.get("oldPassword")
        new_password = request.form.get("newPassword")

        # Validate user exists
        userDetails = db.execute("SELECT * FROM users WHERE username = ?;", username)

        if not userDetails or not check_password_hash(
            userDetails[0]["hash"], old_password
        ):
            return apology("username or password incorrect", 400)

        # Get Hash of Old and New Password
        new_password_hash = generate_password_hash(new_password)

        # Replace old password with new password
        db.execute("UPDATE users SET hash = ? WHERE id = ? AND username = ?;",
                   new_password_hash, userDetails[0]["id"], username)

        # Forget any user_id
        session.clear()

        # Redirect user to login form
        return redirect("/")
    else:
        return render_template("change.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    transaction_list = db.execute("SELECT * FROM history WHERE id = ?;", session["user_id"])
    add_transaction_list = db.execute("SELECT * FROM addHistory WHERE id = ?;", session["user_id"])
    return render_template("history.html", transactionList=transaction_list, addTransactionList=add_transaction_list)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        if not request.form.get("password"):
            return apology("must provide password", 400)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 400)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    if request.method == "POST":
        # Get Form Details
        symbol = request.form.get("symbol").upper()

        # Obtain Stock Details
        stock_details = lookup(symbol)

        # Validate Stock Symbol
        if not stock_details:
            return apology("must provide valid stock symbol", 400)

        # Format price to USD
        stock_details["price"] = usd(stock_details["price"])

        return render_template("quoted.html", stockDetails=stock_details)

    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Validate Password
        if not password or not confirmation:
            return apology("must provide password", 400)

        elif password != confirmation:
            return apology("passwords must match", 400)

        password_hash = generate_password_hash(password)

        # Validate Username
        if not username:
            return apology("must provide username", 400)

        try:
            db.execute("INSERT INTO users (username, hash) VALUES (?, ?);", username, password_hash)
        except ValueError:
            return apology("username already exists", 400)

        return render_template("login.html")

    else:
        # Loads register page upon clicking register button in layout.html
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    # Assumes history and shares table already exist
    if request.method == "POST":
        # Get Form and Session Details
        symbol = request.form.get("symbol").upper()
        try:
            shares = int(request.form.get("shares"))
        except ValueError:
            return apology("must provide valid share count", 400)
        user_id = session["user_id"]

        # Placeholder variable for current amount of shares
        cur_shares = 0

        # Obtain Stock Details
        stock_details = lookup(symbol)

        # Validate Stock Symbol
        if stock_details == None:
            return apology("must provide valid stock symbol", 400)

        # Obtain current stock price
        price = stock_details["price"]

        # Obtain all current stocks and shares of user
        stock_list = db.execute(
            "SELECT stockSymbol, stockShares FROM shares WHERE id = ?;", session["user_id"])

        # Validate ownership of stock and correct shares amount
        isSymbolValid = False
        isSharesValid = False
        for stock in stock_list:
            if stock["stockSymbol"] == symbol:
                isSymbolValid = True
                if stock["stockShares"] >= shares:
                    isSharesValid = True
                    cur_shares = stock["stockShares"]

        if not isSymbolValid:
            return apology("must provide owned stock symbol", 400)

        elif not isSharesValid:
            return apology("must provide valid share amount", 400)

        # Insert transaction details to transaction history table
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        db.execute("INSERT INTO history (id, transactType, stockSymbol, stockPrice, shares, timestamp) VALUES (?, ?, ?, ?, ?, ?);",
                   user_id, "SELL", symbol, price, shares, timestamp)

        # If cur_shares is higher than shares, update shares table
        if cur_shares > shares:
            db.execute(
                "UPDATE shares SET stockShares = stockShares - ? WHERE id = ? AND stockSymbol = ?;", shares, user_id, symbol)

        # If cur_shares is equal to shares, delete row in shares table
        elif cur_shares == shares:
            db.execute(
                "DELETE FROM shares WHERE id = ? AND stockShares = ? AND stockSymbol = ?;", user_id, shares, symbol)

        # Update usser's cash balance
        db.execute("UPDATE users SET cash = cash + ? WHERE id = ?;", price * shares, user_id)

        return redirect("/")

    else:
        # Obtain all current stocks and shares of user
        stock_list = db.execute("SELECT stockSymbol FROM shares WHERE id = ?;", session["user_id"])

        return render_template("sell.html", stockList=stock_list)
