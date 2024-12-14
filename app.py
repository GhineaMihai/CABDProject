from click import command
from flask import Flask
import cx_Oracle

username = 'fambd1r20'
password = 'fambd1r20'
hostname = '193.231.20.20'
hostname_faculta = '172.30.0.13'
port = '15211'
port_faculta = '1521'
sid = 'orcl19c'

connection_string = f'{username}/{password}@{hostname}:{port}/{sid}'
connection = cx_Oracle.connect(connection_string)

cursor = connection.cursor()

def InsertIntoTable (table, table_fields, table_values):
    table_fields_string = "";
    for field in table_fields:
        table_fields_string+=field+', '
    table_fields_string = table_fields_string[:-2];
    table_values_string = "";
    for field in table_values:
        table_values_string+=field+', '
    table_values_string = table_values_string[:-2];

    command = f"INSERT into {table} ({table_fields_string}) VALUES ({table_values_string})"
    cursor.execute(command)
    connection.commit();

def UpdateRow (table, update_fields, update_values, row_name, row_id):
    table_update_fields = "";
    for i in range (len(update_fields)):
        table_update_fields+=update_fields[i] + ' = ' +update_values[i] +', '
    table_update_fields = table_update_fields[:-2];

    command = f"UPDATE {table} SET {table_update_fields} where {row_name} = {row_id}"
    print(command)
    cursor.execute(command)
    connection.commit();

# def CheckIfItIsForeignKey(table, row_name, row_id):
#     cursor.execute(f'SELECT * FROM Assignments where ')

def DeleteRow ( table, row_name, row_id):
    command = f"DELETE FROM {table} where {row_name} = {row_id}"
    print(command)
    cursor.execute(command)
    connection.commit();

#InsertIntoTable("Employees", ["employee_id", "name", "position"], ['211',"'b'", "'b'"])
#UpdateRow("Employees", ["name"], ["'Ana'"], "employee_id", 22)
#UpdateRow("Employees", ["name", "position"], ["'Ana'", "'A'"], "employee_id", 22)
DeleteRow("Employees","employee_id", 211)

cursor.execute('SELECT * FROM Employees')
for row in cursor:
    print(row)
print('------------------------------------------------')
app = Flask(__name__)

# cursor.execute('SELECT * FROM Employees')
# for row in cursor:
#     print(row)
# print('------------------------------------------------')
# cursor.execute("INSERT into Employees (employee_id, name, position) VALUES (123, 'a', 'a2')")
# connection.commit();
cursor.execute('SELECT * FROM Employees')
@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'

cursor.close()
connection.close()

if __name__ == '__main__':
    app.run()
