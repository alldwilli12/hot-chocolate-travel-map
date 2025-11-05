# Hot Chocolate Travel Map
#### Video Demo: https://youtu.be/L-gPSRxuO-k
#### Description:
The **Hot Chocolate Travel Map** is a web application that allows users to track, discover, and share their favorite hot chocolate spots from around the world. It combines Flask, SQLite, Leaflet.js and Bootstrap to create an interactive experience with mapping, user authentication and geolocation. Users can register an account, securely login and add new locations with personalized notes and images, and view all logged locations on an interactive map. The personal travel journal feature also allows users to view and edit their saved hot chocolate spots as a grid of cards. Finally, users have the ability to export data in KML format so locations can be used in Google Maps or Google Earth.

## Setup and Installation
Clone the repository
```bash
  git clone https://github.com/alldwilli12/hot-chocolate-travel-map.git
  cd hot-chocolate-travel-map

Set up a virtual environment
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

Install required packages
Pip install flask requests werkzeug
Run the application
Flask run or python app.py
Access the application
Open the browser and go to http://127.0.0.1:5000/


## File Overview
app.py
This file is the Flask application files that is responsible for all backend logic including initialization of the database; routes for registration, login, logout, adding spots, and exporting data; user authentication and password hashing for extra security; geocoding through OpenStreetMap's Naminatim API; and converting data to JSON format to render markers on the frontend.



## templates/
This folder contains all the HTML templates that are used to render the web pages.

**layout.html** template is the base template that includes the navigation bar, footer, Bootstrap and custom CSS. The subsequent templates extend from this file

**index.html** template both displays the Leaflet map and contains JavaScript that retrieves and plots all saved hot chocolate spots.

**add_spot.html** provides the forms where users can add new hot chocolate spots. The  form contains fields for the hot chocolate spot name, address, rating, optional notes, optional date traveled, and optional image upload.

**journal.html** displays a user's hot chocolate spots as small cards in a grid. Each card shows the name, rating, address and photo of the hot chocolate spot if available.

Together **login.html** and **register.html** allow for user authentication. For added security, passwords are hashed.

**about.html** displays a description of the site's purpose.



## static/js/script.js
This JavaScript file is responsible for the interactivity of the hot chocolate travel map.

The file initializes the Leaflet map, fetches hot chocolate spot data from Flask using /spots and /my_spots, and generates the markers on the map. The popup of each marker displaces a hot chocolate's spots name, address, rating, notes, and image. There is also a feature of a toggle button which allows logged-in users to switch between seeing all users' spots and just their own.



## static/css/style.css
This style sheet provides the consistent warm cozy café aesthetic throughout the site. While bootstrap helps with the responsiveness and layout of the site, the CSS file adjusts the map dimensions, text styling, popups and toggle buttons


### Database
SQLite is used and the database **cozy.db** is generated automatically when the application is first launched through the int_db() function in app.py. Two tables are included in the database.

The users table contains columns id, username, and hash which prevents the passwords from being stored in plain text.

The spots table contains the columns id, user_id, name, address, rating, notes, lat, lon, image_path, and data travel. This table has hot chocolate spot data and is linked with the user who added the data.




## Overview of Functionality

**Add Spot**: Users can add new hot chocolate spots including address, rating, optional notes, optional date traveled, and optional photos

**Geocoding** : OpenStreetMap's Nominatim API is used to convert addresses into coordinates. If the geocoding fails, a flash message is used to notify the user. The spot will still be stored and appear on the personal travel journal but it will not appear on the map.

**Interactive Map** : All stored hot chocolate spots are displayed as markers with popups on the Leaflet map.

**Personal Hot Chocolate Travel Journal** : Users can view and edit the cards of their saved hot chocolate spots.

**Export to KML**  : Users have the ability to export locations as.kml files that that can be viewed in Google Maps or Google Earth

**Filtering** : Users can toggle between their stops and all user's spots




## Design Decisions

Leaflet.js and OpenStreetMap were used instead of Google Maps API to keep the project open-source.

A single /spots route was chosen instead of having separate routes for all and individual users  to prevent redundant code. The single route handles both cases depending on the status of a URL query parameter.

Image uploads were restricted to safe file types and locally stored in a static/uploads directory.

Finally, in order to make setup easier the database and uploads folder are automatically created with application is first run.



## Reflections and Future Improvements
In the future, the application could include features that allow users to delete existing entries, comment or like other users and spots, filter by location or rating.

## Acknowledgements
The Hot Chocolate Travel Map was created for the CS50x Final Project. Thank you to the CS50 staff for providing instruction in programming, Flask and SQL. Also, thank you to OpenSteetMap for providing geolocation data that was used in rending the map and geocoding. Finally, assistance was also used from ChatGPT as a tool for refining code structure, some debugging and explaining design concepts. However all code, design decisions and implementations were reviewed and implemented by the author of this project.

