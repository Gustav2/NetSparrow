import MySQLdb
import os
import time

# Load environment variables
DB_HOST = os.getenv('DB_HOST', 'db')
DB_USER = os.getenv('DB_USER', 'myproject_user')
DB_PASSWD = os.getenv('DB_PASSWORD', 'my_user_password')
DB_NAME = os.getenv('DB_NAME', 'netsparrow_db')

# Wait for the MySQL server to be ready
while True:
    try:
        # Establish a connection to the database
        dataBase = MySQLdb.connect(
            host=DB_HOST,
            user=DB_USER,
            passwd=DB_PASSWD
        )
        print("Database connection established.")
        break  # Exit loop if connection is successful
    except MySQLdb.OperationalError:
        print("Waiting for the database to be ready...")
        time.sleep(2)

# Create a cursor object
cursorObject = dataBase.cursor()

# Execute the SQL command to create the database
cursorObject.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")

print(f"Database '{DB_NAME}' created successfully!")

# Close the connection
cursorObject.close()
dataBase.close()