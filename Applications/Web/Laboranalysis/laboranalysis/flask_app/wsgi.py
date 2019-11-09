#!/usr/bin/python3.7

# Import our application
from application import app

# Checks importing issue
if __name__ == "__main__":
    # Run application in debug mode
    app.run( debug=True, 
             host='0.0.0.0' )
