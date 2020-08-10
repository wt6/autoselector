# AutoSelector

By Wesley Thompson

## Description

* This project is a web application called AutoSelector.
* With this website, users can submit information on vehicles they have purchased such as milage at purchase, maintenance cost and purchase price.
* Users are able to lookup vehicle make and models to get a graph of the estimated depreciation and tabulated data such as maintenance cost by age.

## How to Use
1. Clone the autoselector repository.

2. **(For testing purposes)** By default the application will use a non-secret development key for signing session cookies. This is stored in the default settings file. As this is part of the publicly visible code, this is only suitable for use when testing.

    **(For non-testing purposes)** A config file should be created containing "SECRET_KEY = ####" where #### is a long random string of bytes. This key should ideally be created using a cryptographic random generator. Once created the file location should be set to environment variable 'AUTOSELECTOR_SETTINGS' in order for the application to load the key.

3. **(For testing purposes)** Flask's inbuilt development server can be used by setting the environment variable FLASK_APP=application.py. Then run using command 'flask run' and direct your web browser to the provided IP address to use the website.

    **(For non-testing purposes)** A WSGI server will be required to run web application.

## Prerequisites
* Python 3.5
* Flask (can be installed via pip)

## Implementation
* Python application using Flask web micro-framework.
* Google charts service used for generating graphs via javascript.
* Bootstrap (available under the MIT licence), is used for generating the navigation bar as well as other webpage styline elements.
* HTML used in combination with Jinja 2 for webpage templates.
* CSS used for webpage styling.
* SQLite database used for storing user and vehicle data.

### Currency and Inflation Adjustment

* This website is setup for the united kingdom, so the currency is set to GBP, there is currently no option for other currencies.
* The values of purchase price and maintenance cost for reviews based on purchases from past years are adjusted for inflation using values from the UK Office for National Statistics website.
* Inflation is calculated from index values stored in a comma seperated values file called 'inflation.csv'.
* This file will need updating annually with the previous years inflation index value.
* If this file is missing an index value for a required year, the application will find the nearest year available with an index value available and use that value.