import csv

from flask import redirect, session
from functools import wraps

def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


class InflationFinder(object):
    """Class for object which looks-up inflation index value for given year."""

    def __init__(self):
        # Get inflation (CPI) index value data from CSV file.
        # Data in this file is taken from the UK Office for National Statistics website:
        # https://www.ons.gov.uk/economy/inflationandpriceindices/datasets/consumerpriceinflation
        with open("inflation.csv", "r") as inflation_file:
            datareader = csv.reader(inflation_file)

            # Save data from inflation file into dict
            self.data = {}
            for line in datareader:
                self.data[int(line[0])] = float(line[1])

    def lookup(self, year):
        """Method returns inflation index value for given year."""
        index = None
        if self.data.get(year) != None:
            index = self.data[year]

        # if dictionary is empty provide index value of 100 (if all index values use 100 no inflation adjustment occurs)
        elif len(self.data) == 0:
            index = 100

        # If dictionary not empty find nearest available year's index value
        else:
            for i in range(1, 15):
                if self.data.get(year+i) != None:
                    index = self.data[year+i]
                elif self.data.get(year-i) != None:
                    index = self.data[year-i]
                if index != None:
                    break
        if index == None:
            index = 100
        return index

def comma_format(value):
    """Formats value with commas and returns new value."""
    return f"{value:,}"
