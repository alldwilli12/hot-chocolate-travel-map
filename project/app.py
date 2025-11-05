import sqlite3
import requests
import os
from flask import Flask, render_template, jsonify, request, redirect, flash, session, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "super_secret_key"

# Image upload setup
UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Make sure uploads folder exists too
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


DATABASE = "cozy.db"
# Automatically create the database and tables if they don't exist
def init_db():
    if not os.path.exists(DATABASE):
        print(" Creating database...")
        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                hash TEXT NOT NULL
            );
        """)
        cur.execute("""
            CREATE TABLE spots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT NOT NULL,
                address TEXT,
                rating REAL,
                notes TEXT,
                lat REAL,
                lon REAL,
                image_path TEXT,
                date_traveled TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
        """)
        conn.commit()
        conn.close()
        print(" Database created successfully.")
    else:
        print(" Database already exists.")



# ensure valid file extension (ie. .jpg, .png)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_db_connection():
    conn = sqlite3.connect(DATABASE)  # connects to database
    conn.row_factory = sqlite3.Row  # makes results act like dictionaries instead of getting results as a tuple
    return conn


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/spots")
def get_spots():
    user_id = session.get("user_id")  # check if user is logged in
    mine_only = request.args.get("mine")  # checks if ?mine=1 is in the URL

    conn = get_db_connection()
    if mine_only and user_id:
        # show only logged in user's spots
        spots = conn.execute(
            "SELECT * FROM spots WHERE user_id = ?", (user_id,)
        ).fetchall()
    else:
        # show all user's spots
        spots = conn.execute("SELECT * FROM spots").fetchall()

    conn.close()
    return jsonify([dict(row) for row in spots])


@app.route("/add", methods=["GET", "POST"])
def add_spot():
    if request.method == "POST":
        name = request.form.get("name")
        address = request.form.get("address")
        rating = request.form.get("rating")
        notes = request.form.get("notes")
        date_traveled = request.form.get("date_traveled")
        user_id = session.get("user_id")  # userid of logged in user

        # Handle optional image
        image = request.files.get("image")
        image_path = None
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            image_path = f"uploads/{filename}"

        # Geocode address (convert an address to a geographic coordinate)
        lat = lon = None
        if address:
            try:
                url = f"https://nominatim.openstreetmap.org/search?q={address}&format=json"
                headers = {"User-Agent": "CozyMapApp/1.0"}
                res = requests.get(url, headers=headers, timeout=10)
                if res.status_code == 200:
                    data = res.json()
                    if data:
                        lat, lon = data[0]["lat"], data[0]["lon"]
                    else:
                        flash("Couldn't find that address — spot saved without a map pin.")
                else:
                    flash("Address lookup failed. Spot saved without map location.")
            except requests.RequestException:
                flash("Geocoding service unavailable. Spot saved without location.")

        # Save location in the spots table of the cozy database
        conn = get_db_connection()
        conn.execute("""
            INSERT INTO spots (name, address, rating, notes, lat, lon, user_id, image_path, date_traveled)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, address, rating, notes, lat, lon, user_id, image_path, date_traveled))
        conn.commit()  # permanently saves changes in database
        conn.close()  # closes the database connection

        # Redirect to home page
        flash("New cozy spot added! ☕")
        return redirect("/")

    # If GET, show the form
    return render_template("add_spot.html")


@app.route("/my_spots")
def my_spots():
    if "user_id" not in session:
        return jsonify([])  # not logged in — return nothing

    conn = get_db_connection()
    spots = conn.execute(
        "SELECT * FROM spots WHERE user_id = ?", (session["user_id"],)
    ).fetchall()
    conn.close()
    return jsonify([dict(row) for row in spots])


@app.route("/export")
def export_spots():
    """Export user's spots as a Google Maps-compatible KML file."""
    if "user_id" not in session:
        flash("Please log in to export your spots.")
        return redirect("/login")

    conn = get_db_connection()
    spots = conn.execute(
        "SELECT name, address, rating, notes, lat, lon, date_traveled FROM spots WHERE user_id = ?",
        (session["user_id"],)
    ).fetchall()
    conn.close()

    # Build KML content
    kml_header = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Cozy Hot Chocolate Spots</name>
"""
    kml_body = ""
    for s in spots:
        if s["lat"] and s["lon"]:
            kml_body += f"""
    <Placemark>
      <name>{s["name"]}</name>
      <description>
        <![CDATA[
        <b>Address:</b> {s["address"]}<br>
        <b>Rating:</b> {s["rating"]}/5<br>
        <b>Notes:</b> {s["notes"] or "None"}<br>
        <b>Date Traveled:</b> {s["date_traveled"] or "N/A"}
        ]]>
      </description>
      <Point>
        <coordinates>{s["lon"]},{s["lat"]},0</coordinates>
      </Point>
    </Placemark>
"""
    kml_footer = """
  </Document>
</kml>
"""

    kml_data = kml_header + kml_body + kml_footer

    # Return as downloadable file
    response = make_response(kml_data)
    response.headers["Content-Type"] = "application/vnd.google-earth.kml+xml"
    response.headers["Content-Disposition"] = "attachment; filename=cozy_hot_chocolate_spots.kml"
    return response


@app.route("/export_all")
def export_all_spots():
    conn = get_db_connection()
    spots = conn.execute("SELECT * FROM spots WHERE lat IS NOT NULL AND lon IS NOT NULL").fetchall()
    conn.close()

    # Build KML content
    kml_header = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Cozy Hot Chocolate Spots</name>
"""
    kml_body = ""
    for s in spots:
        if s["lat"] and s["lon"]:
            kml_body += f"""
    <Placemark>
      <name>{s["name"]}</name>
      <description>
        <![CDATA[
        <b>Address:</b> {s["address"]}<br>
        <b>Rating:</b> {s["rating"]}/5<br>
        <b>Notes:</b> {s["notes"] or "None"}<br>
        <b>Date Traveled:</b> {s["date_traveled"] or "N/A"}
        ]]>
      </description>
      <Point>
        <coordinates>{s["lon"]},{s["lat"]},0</coordinates>
      </Point>
    </Placemark>
"""
    kml_footer = """
  </Document>
</kml>
"""

    kml_data = kml_header + kml_body + kml_footer

    # Return as downloadable file
    response = make_response(kml_data)
    response.headers["Content-Type"] = "application/vnd.google-earth.kml+xml"
    response.headers["Content-Disposition"] = "attachment; filename=cozy_hot_chocolate_spots.kml"
    return response


@app.route("/register", methods=["GET", "POST"])
def register():
    # Register User#
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            flash("Must provide username")
            return redirect("/register")

        # Ensure password was submitted
        elif not request.form.get("password"):
            flash("Must provide username")
            return redirect("/register")

        # Ensure password verification was submitted
        elif not request.form.get("confirmation"):
            flash("Must confirm password")
            return redirect("/register")

        # Ensure password and password verification are the same
        elif request.form.get("password") != request.form.get("confirmation"):
            flash("passwords must match")
            return redirect("/register")

        # Ensure username is not taken
        # Query database for username
        conn = get_db_connection()
        row = conn.execute(
            "SELECT * FROM users WHERE username = ?", (request.form.get("username"),)
        ).fetchone()

        if row:
            conn.close()
            flash("Choose another username. Username already taken")
            return redirect("/register")

        # Add user to users table of database
        # Never store plaintext password. Generate hash of password
        hash_password = generate_password_hash(
            request.form.get("password"), method='pbkdf2', salt_length=8
        )

        # Add user to Database
        cursor = conn.execute(
            "INSERT INTO users (username, hash) Values (? , ?)",
            (request.form.get("username"), hash_password)
        )
        new_user_id = cursor.lastrowid

        conn.commit()  # permanently saves changes in database
        conn.close()  # closes the database connection

        # Log in user

        session["user_id"] = new_user_id

        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    # Display Form
    else:
        return render_template("register.html")


@app.route("/journal")
def journal():
    if "user_id" not in session:
        flash("Please log in to view your travel journal.")
        return redirect("/login")

    conn = get_db_connection()
    spots = conn.execute(
        "SELECT * FROM spots WHERE user_id = ? ORDER BY id DESC",
        (session["user_id"],)
    ).fetchall()
    conn.close()

    return render_template("journal.html", spots=spots)


@app.route("/edit/<int:spot_id>", methods=["GET", "POST"])
def edit_spot(spot_id):
    # Require login
    if "user_id" not in session:
        flash("Please log in to edit your spots.")
        return redirect("/login")

    conn = get_db_connection()
    spot = conn.execute(
        "SELECT * FROM spots WHERE id = ? AND user_id = ?",
        (spot_id, session["user_id"])
    ).fetchone()

    if not spot:
        conn.close()
        flash("Spot not found or you don't have permission to edit it.")
        return redirect("/journal")

    # POST = update record
    if request.method == "POST":
        name = request.form.get("name")
        address = request.form.get("address")
        rating = request.form.get("rating")
        notes = request.form.get("notes")
        date_traveled = request.form.get("date_traveled")

        # Optional: update image
        image = request.files.get("image")
        image_path = spot["image_path"]
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            image_path = f"uploads/{filename}"

        # Optional: update coordinates if address changed
        lat, lon = spot["lat"], spot["lon"]
        if address != spot["address"]:
            try:
                url = f"https://nominatim.openstreetmap.org/search?q={address}&format=json"
                headers = {"User-Agent": "CozyMapApp/1.0"}
                res = requests.get(url, headers=headers, timeout=10)
                if res.status_code == 200 and res.json():
                    data = res.json()[0]
                    lat, lon = data["lat"], data["lon"]
            except Exception:
                flash("Couldn't update coordinates for new address.")

        # Update database
        conn.execute("""
            UPDATE spots
            SET name=?, address=?, rating=?, notes=?, date_traveled=?, image_path=?, lat=?, lon=?
            WHERE id=? AND user_id=?
        """, (name, address, rating, notes, date_traveled, image_path, lat, lon, spot_id, session["user_id"]))
        conn.commit()
        conn.close()

        flash("Spot updated successfully!")
        return redirect("/journal")

    conn.close()
    return render_template("edit_spot.html", spot=spot)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        print("Form submitted:", request.form.get("username"))
        # Ensure username was submitted
        if not request.form.get("username"):
            flash("must provide username")
            return redirect("/login")

        # Ensure password was submitted
        elif not request.form.get("password"):
            flash("must provide password")
            return redirect("/login")

        # Query database for username
        conn = get_db_connection()
        rows = conn.execute(
            "SELECT * FROM users WHERE username = ?", (request.form.get("username"),)
        ).fetchall()
        conn.close()

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            flash("invalid username and/or password")
            return redirect("/login")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        flash("Welcome back!")
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


if __name__ == "__main__":
    init_db()  # Ensure database exists before running
    app.run(debug=True)

