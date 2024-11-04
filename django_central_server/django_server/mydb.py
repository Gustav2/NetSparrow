# Dokument for creating a database in MySQL using Python [Terminal: python3 mydb.py]
import MySQLdb

dataBase = MySQLdb.connect(
    host = 'localhost',
    user = 'user',
    passwd = 'password1234'

)

cursorObject = dataBase.cursor()

cursorObject.execute("CREATE DATABASE netsparrow_db")

print("Worked!")

