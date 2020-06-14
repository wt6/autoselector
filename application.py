from datetime import datetime

from flask import Flask, flash, redirect, render_template, request, session, jsonify
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import InflationFinder, login_required, comma_format
from dbmanager import DBManager

# Global variable for location of db which stores user, vehicle and reviews data
db_location = "autos.db"

# Configure application
app = Flask(__name__)


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Initialise DBManager object
db = DBManager(app, db_location)

@app.route("/")
def index():
    """Render index template Showing options"""

    # Find three most commonly reviewed vehicles then retrieve make and model names
    ordered = db.execute("SELECT vehicle_id FROM reviews GROUP BY vehicle_id ORDER BY COUNT(vehicle_id) DESC")
    popular = []
    for i in range(3):
        vehicle = db.execute("SELECT make, model FROM vehicles WHERE id = :vehicle_id", vehicle_id=ordered[i]["vehicle_id"])
        name = vehicle[0]["make"] + " " + vehicle[0]["model"]
        link = f"/estimate?make={vehicle[0]['make']}&model={vehicle[0]['model']}"
        vehicle = {"name":name, "link":link}
        popular.append(vehicle)

    # Check if the user is logged_in
    if session.get("user_id"):
        logged_in = True
    else:
        logged_in = False
    return render_template("index.html", popular=popular, logged_in=logged_in)

@app.route("/new", methods=["GET", "POST"])
@login_required
def new():
    """Render template for registering new vehicle"""

    if request.method == "GET":
        return render_template("new.html")

    elif request.method == "POST":

        # Ensure both make and model of vehicle are provided
        make = request.form.get("make")
        model = request.form.get("model")
        if make == "": flash("Please enter make of vehicle"); return redirect("/new")
        if model == "": flash("Please enter model of vehicle"); return redirect("/new")

        # Ensure only first letter is capatilised
        make = make.title()
        model = model.title()

        # Check if vehicle alredy in database
        check = db.execute("SELECT * FROM vehicles WHERE make = :make AND model = :model", make=make, model=model)
        if check:
            flash("Vehicle already registered")
            return redirect("/review")

        # If not present add vehicle to database and notify user if executed sucessfully
        else:
            if not db.execute("INSERT INTO vehicles (make, model) VALUES (:make, :model)", make=make, model=model):
                flash("Error, vehicle could not be registered")
                return redirect("/new")
            else:
                flash("Vehicle added successfully")
                return redirect("/review")

@app.route("/review", methods=["GET", "POST"])
@login_required
def review():
    """Render template for writing review or submit review"""

    if request.method == "GET":

        # Get list of distinct vehicle makes
        rows = db.execute("SELECT DISTINCT make FROM vehicles")
        makes = []
        for row in rows:
            makes.append(row['make'])

        # Create list of last 15 years to populate model year option box
        current_year = datetime.now().year
        years = [current_year-i for i in range(16)]

        return render_template("review.html", makes=makes, years=years)

    elif request.method == "POST":

        # Take submited fields from form and ensure entered data is appropriate
        make = request.form.get("make")
        if not make or make == "none": flash("Please select make"); return redirect("/review")
        model = request.form.get("model")
        if not model or model == "none": flash("Please select model"); return redirect("/review")
        model_year = request.form.get("model_year")
        if not model_year or model_year == "none": flash("Please select model year"); return redirect("/review")
        purchase_year = request.form.get("purchase_year")
        if not purchase_year or purchase_year == "none": flash("Please select purchase year"); return redirect("/review")

        # Check integer value greater than 0 entered for mileage
        purchase_mileage = request.form.get("purchase_mileage")
        if purchase_mileage == "": flash("Please enter purchase mileage"); return redirect("/review")
        elif not int(purchase_mileage) > 0: flash("Purchase mileage must be a positive integer"); return redirect("/review")

        # Check price entered is not negative
        purchase_price = request.form.get("purchase_price")
        if purchase_price == "": flash("Please enter purchase price"); return redirect("/review")
        elif float(purchase_price) < 0: flash("Purchase price must be greater than £0"); return redirect("/review")

        # Check if car is currently owned and convert to boolean
        ownership = request.form.get("own")
        if ownership == 'yes':
            ownership = 1
        else:
            ownership = 0

        # If car is currently owned get annual maintenance cost from form and verify value
        if ownership:
            annual_maintenance = request.form.get("annual_maintenance")
            if annual_maintenance == "": flash("Please enter maintenance cost for last year"); return redirect("/review")
            elif float(annual_maintenance) < 0: flash("Maintenance cost must be positive, in £"); return redirect("/review")
            annual_maintenance = int(annual_maintenance)
        else:
            annual_maintenance = None

        # Retrieve vehicle_id from database
        vehicle_id = db.execute("SELECT id FROM vehicles WHERE make = :make AND model = :model", make=make, model=model)[0]["id"]

        # Check user has not already submitted a review for this vehicle
        previous_reviews = db.execute("SELECT review_date FROM reviews WHERE vehicle_id=:vehicle_id AND user_id=:user_id AND\
                                    model_year=:model_year AND purchase_year=:purchase_year AND purchase_mileage=:purchase_mileage\
                                    AND purchase_price=:purchase_price", vehicle_id=vehicle_id, user_id=session["user_id"],
                                    model_year=int(model_year), purchase_year=int(purchase_year),
                                    purchase_mileage=int(purchase_mileage), purchase_price=int(purchase_price))

        if len(previous_reviews) != 0:
            message = f"You already reviewed this vehicle on: {previous_reviews[0]['review_date']}!"
            flash(message)
            return redirect("/")

        # Create record in database for review
        db.execute("INSERT INTO reviews (vehicle_id, user_id, model_year, purchase_year, purchase_mileage, purchase_price, ownership, annual_maintenance)\
                    VALUES (:vehicle_id, :user_id, :model_year, :purchase_year, :purchase_mileage, :purchase_price, :ownership, :annual_maintenance)",
                    vehicle_id=vehicle_id, user_id=session["user_id"], model_year=int(model_year), purchase_year=int(purchase_year),
                    purchase_mileage=int(purchase_mileage), purchase_price=int(purchase_price), ownership=ownership, annual_maintenance=annual_maintenance)

        # Flash success message and return to index page
        flash("Thank you for submitting a review!")
        return redirect("/")

@app.route("/estimate", methods=["GET", "POST"])
def estimate():
    """Render template for selecting vehicle and return results upon submission"""

    # Get current year for populating model year selection boxes and calculating age
    current_year = datetime.now().year

    if request.method == "GET":

        # Get chosen make and model if query string used
        qmake = request.args.get("make", None)
        qmodel = request.args.get("model", None)

        # Get list of distinct vehicle makes
        rows = db.execute("SELECT DISTINCT make FROM vehicles")
        makes = []
        for row in rows:
            makes.append(row['make'])

        # Create list of last 15 years to populate model year option box
        years = [current_year-i for i in range(16)]
        return render_template("estimate.html", makes=makes, years=years, qmake=qmake, qmodel=qmodel)

    elif request.method == "POST":
        make = request.form.get("make")
        model = request.form.get("model")
        model_year = request.form.get("model_year")

        # Ensure all fields are filled out
        if make == "none": flash("Please select a make"); return redirect("/estimate")
        if model == "none": flash("Please select a model"); return redirect("/estimate")
        if model_year == "none": flash("Please select a model year"); return redirect("/estimate")

        # Get age of vehicle
        selected_age = current_year - int(model_year)

        # Find vehicle id
        vehicle_id = db.execute("SELECT id FROM vehicles WHERE make = :make AND model = :model",
                                                                                        make=make,
                                                                                        model=model)[0]["id"]

        # Lookup database for values for particular vehicle
        rows = db.execute("SELECT * FROM reviews WHERE vehicle_id = :vehicle_id", vehicle_id=vehicle_id)

        if not rows:
            flash("Sorry, no data is available for this vehicle yet")
            return redirect("/estimate")

        # Use retrieved records from database to assemble list of value by year
        # Assemble list with index number corresponding to age in years
        # Each list item of 'values' is a list of different values for vehicles of that age
        values = []
        spend = []
        for i in range(16):
            values.append([])
            spend.append([])

        # Initialise InflationFinder object then get inflation index value for current year
        inflation = InflationFinder()
        current_inflation = inflation.lookup(current_year)

        for row in rows:

            # If vehicle age is greater than 15 data will not be used, skip next row
            model_year = row["model_year"]
            if current_year - model_year > 15:
                continue

            purchase_year = row["purchase_year"]
            review_year = int(row["review_date"][:4])
            price = row["purchase_price"]
            annual_maintenance = row["annual_maintenance"]
            purchase_age = purchase_year - model_year
            review_age = review_year - model_year

            # Use inflation index values data to calculate current day equivalent purchase price and maintenance cost
            # then append value to 'values' and 'spend' lists
            price = price * (current_inflation / inflation.lookup(purchase_year))
            values[purchase_age].append(price)
            if annual_maintenance != None:
                annual_maintenance = annual_maintenance * (current_inflation / inflation.lookup(review_year))
                spend[review_age].append(annual_maintenance)

        # list named 'depreciation' used to store average values by age in years.
        depreciation = []
        for year in values:
            if len(year) == 0:
                depreciation.append("unavailable")
            else:
                total = 0
                for value in year:
                    total += value
                depreciation.append(round(total/len(year)))

        # annual percentage depreciation rate for each year calculated and stored in list called 'rate'
        rate = [0]  # depreciation rate for 0th year is 0%
        for i in range(1, 16):
            if depreciation[i] == 'unavailable' or depreciation[i-1] == 'unavailable' or depreciation[i-1] == 0:
                rate.append("unavailable")
            else:
                rate.append(int(100 - (depreciation[i] / depreciation[i-1]) * 100))

        # list named 'maintenance' used to store average annual maintenance cost by age in years.
        maintenance = []
        for year in spend:
            if len(year) == 0:
                maintenance.append("unavailable")
            else:
                total = 0
                for value in year:
                    total += value
                maintenance.append(round(total/len(year)))

        return render_template("result.html", make=make, model=model, selected_age=selected_age, depreciation=depreciation, rate=rate, maintenance=maintenance)


@app.route("/history", methods=["GET"])
@login_required
def history():
    """Query database to find previous reviews by current user and render /history page with this data"""

    # Query database for previous reviews
    history = db.execute("SELECT vehicle_id, Model_year, purchase_year, purchase_mileage, purchase_price, annual_maintenance,\
                        ownership, review_date FROM reviews WHERE user_id = :user_id ORDER BY review_date DESC",
                        user_id=session["user_id"])

    # for retrived reviews find vehicle make and model and insert in dict. 'vehicle_id' is removed from dict.
    for review in history:
        vehicle_data = db.execute("SELECT make, model FROM vehicles WHERE id = :vehicle_id", vehicle_id=review.pop("vehicle_id", None))
        if len(vehicle_data) == 1:
            review["make_model"] = vehicle_data[0]["make"] + " " + vehicle_data[0]["model"]
        elif len(vehicle_data) > 1:
            print("Error: duplicate 'vehicle_id' in 'vehicles' table of database")
            review["make_model"] = "Error finding vehicle data"
        else:
            print("Error: 'vehicle_id' for historical vehicle review not present in 'vehicles' table of database")
            review["make_model"] = "Error finding vehicle data"

        # Format numbers with commas seperating into thousands using helper function
        review["purchase_price"] = comma_format(review["purchase_price"])
        review["purchase_mileage"] = comma_format(review["purchase_mileage"])
        if review["annual_maintenance"]:
            review["annual_maintenance"] = comma_format(review["annual_maintenance"])

    # Render history page passing in 'history' with historical review data to be used in a table
    return render_template("history.html", history=history)


@app.route("/get_models")
def get_models():
    """Assemble list of models for specified make and return as JSON"""
    make = request.args.get("make")
    rows = db.execute("SELECT model FROM vehicles WHERE make = :make", make=make)
    models = [row["model"] for row in rows]
    return jsonify(models)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id and username
    session.pop("user_id", None)
    session.pop("username", None)

    # User reached route via GET request, render login page
    if request.method == "GET":
        return render_template("login.html")

    # User submitted login details via POST, check details against database
    else:

        # Check username was provided
        if not request.form.get("username"):
            flash("Please enter a username")
            return redirect("/login")

        # Check password was provided
        elif not request.form.get("password"):
            flash("Please enter a username and password")
            return redirect("/login")

        # Lookup username in database
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Check username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["password"], request.form.get("password")):
            flash("Username and password combination not valid! Please try again or click register.")
            return redirect("/login")

        # Store userid and username in session object
        session["user_id"] = rows[0]["id"]
        session["username"] = rows[0]["username"]

        # Redirect user to home page
        flash("Login successful")
        return redirect("/")


@app.route("/logout")
def logout():
    """Log user out"""

    # Clear session data
    session.clear()

    # Return user to index page
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Display page with registration form
    if request.method == "GET":
        return render_template("register.html")

    # Attempt to register user
    else:

        # Get details from registration form
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Ensure username, password and password confirmation were provided
        if not username:
            flash("Please enter a username!")
            return redirect("/register")
        elif not password:
            flash("Please enter a password!")
            return redirect("/register")
        elif not confirmation:
            flash("Please enter you password again in the confirmation box!")
            return redirect("/register")

        # Ensure password matches password confirmation
        elif password != confirmation:
            flash("Passwords entered do not match! please try again.")
            return redirect("/register")

        # Warn user if username is already taken
        result = db.execute("SELECT id FROM users WHERE username = :username", username=username)
        if result != []:
            flash("Username already in use, please enter a different username")
            return redirect("/register")

        # Add user to database
        pass_hash = generate_password_hash(password)
        result = db.execute("INSERT INTO users (username, password) VALUES (:username, :password)",
                            username=username, password=pass_hash)

        # Log user in
        session["user_id"] = result
        session["username"] = username
        flash("Registration successful")
        return redirect("/")


@app.route("/passchange", methods=["GET", "POST"])
@login_required
def change_password():
    """Allow user to change password"""

    # Render page with change password form
    if request.method == "GET":
        return render_template("passchange.html")

    # Verify current password and check new passwords match
    else:

        # Find hashed password for current user from database and check against password entered in form
        verify = db.execute("SELECT password FROM users WHERE id == :user", user=session["user_id"])[0]["password"]
        if not check_password_hash(verify, request.form.get("curr_password")):
            flash("Current password incorrect!")
            return redirect("/passchange")

        # Check new password matches confirmation field
        if request.form.get("password") != request.form.get("confirmation"):
            flash("New passwords entered do not match! Please try again.")
            return redirect("/passchange")

        # Check new password is not the same as the current password
        if check_password_hash(verify, request.form.get("password")):
            flash("New password must be different from current password")
            return redirect("/passchange")

        # Update database with new password in hashed form
        db.execute("UPDATE users SET password = :password WHERE id = :user",
                   password=generate_password_hash(request.form.get("password")),
                   user=session["user_id"])

        # Redirect to index page
        flash("Password Updated Successfully")
        return redirect("/")

