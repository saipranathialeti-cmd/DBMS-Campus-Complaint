CAMPUS COMPLAINT MANAGEMENT SYSTEM — FLASK + MYSQL

1. Make sure MySQL Server is installed and running.
2. Open this project folder in VS Code.
3. Open schema.sql in MySQL Workbench (or your MySQL query tool) and execute it.
   It creates database campus_complaints and the required tables.
4. Open app.py and edit DB_CONFIG:
   - user: your MySQL username (often root)
   - password: your MySQL password
5. Open VS Code Terminal in this project folder and run:

   py -m pip install -r requirements.txt
   py app.py

6. Open this address in your browser:
   http://127.0.0.1:5000

IMPORTANT:
- Do not double-click index.html. Open the website through the Flask address above.
- HTML/JavaScript sends requests to Python; Python stores and reads data from MySQL.
- The dashboard currently acts as the staff/admin dashboard. Add login and role restrictions
  before using this for real campus data.
