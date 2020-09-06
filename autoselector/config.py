from pathlib import Path

def abs_path(rel_path):
    return str(Path(__file__).parent.resolve()) + "/" + rel_path

# Location of db which stores user, vehicle and reviews data
db_location = abs_path("autos.db")

# Location of CSV file containing annual inflation data
inflation_file_location = abs_path("inflation.csv")
