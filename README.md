This project is a web application called AutoSelector. It allows users to submit reviews of
vehicles they have purchased giving information such as milage at purchase, maintenance cost
and purchase price. Users can then lookup vehicle make and models to get a graph of the
depreciation and tabulated data such as maintenance cost by age.

This website runs using flask and Jinja 2 for templating. Google charts is used for generating
graphs through javascript. Bootstrap, which is available under the MIT licence, is used for
styling the pages and generating the navbar. Data for users reviews is stored in a database
called 'autos.db'.

This website is setup for the united kingdom and so the currency is GBP. The values of purchase
price and maintenance cost for reviews based on purchases from past years are adjusted for
inflation. Adjustment for inflation is calculated from index values stored in a comma seperated
values file called 'inflation.csv', the values in this are taken from the UK Office for National
Statistics website. In future years this will have to be updated to have new years inflation
index values added, otherwise if not updated the appication will find the nearest year available
with an index value and use that value instead.