from click import command
from flask import Flask, render_template, request, redirect, url_for
import cx_Oracle

username = 'fambd1r20'
password = 'fambd1r20'
hostname = '193.231.20.20'
port = '15211'
sid = 'orcl19c'

print(cx_Oracle.version)
cx_Oracle.clientversion()

connection_string = f'{username}/{password}@{hostname}:{port}/{sid}'
connection = cx_Oracle.connect(connection_string)

cursor = connection.cursor()

def SelectFromTable (table, cursor):
    cursor.execute(f'SELECT * FROM {table}')
    rows = cursor.fetchall()
    columns = [col[0] for col in cursor.description]  # Get column names
    return {"columns": columns, "rows": rows}

def SelectRowFromTable (table, id_column, id_value):
    cursor.execute(f'SELECT * FROM {table} where {id_column} = {id_value}')
    for row in cursor:
        print(row)
    print('------------------------------------------------')

def InsertIntoTable(table, table_fields, table_values):
    table_fields_string = ", ".join(table_fields)  # Join field names
    table_values_string = ", ".join([f"'{value}'" for value in table_values])  # Join values and quote them

    # Create the insert command
    command = f"INSERT INTO {table} ({table_fields_string}) VALUES ({table_values_string})"
    cursor.execute(command)
    connection.commit()

def UpdateRow (table, update_fields, update_values, row_name, row_id):
    table_update_fields = "";
    for i in range (len(update_fields)):
        table_update_fields+=update_fields[i] + ' = ' +update_values[i] +', '
    table_update_fields = table_update_fields[:-2];

    command = f"UPDATE {table} SET {table_update_fields} where {row_name} = {row_id}"
    print(command)
    cursor.execute(command)
    connection.commit();

def DeleteRow ( table, row_name, row_id):
    command = f"DELETE FROM {table} where {row_name} = {row_id}"
    print(command)
    cursor.execute(command)
    connection.commit();

def GetHistory (table):
    cursor.execute(f'SELECT * FROM {table}_History')
    for row in cursor:
        print(row)
    print('------------------------------------------------')

def GetTopBugetForProject(project_id):
    cursor.execute(f"""With top_budget as( SELECT project_id, project_name, budget, action, transaction_start, transaction_end,
            CASE
                WHEN transaction_end IS NULL THEN (SYSDATE - transaction_start)
                ELSE (transaction_end - transaction_start)
            END AS perioada
            FROM Projects_History
            ORDER BY budget DESC)
        SELECT b.project_id, b.project_name, b.budget, b.action, b.transaction_start, b.transaction_end, b.perioada
        FROM Projects_History p JOIN top_budget b ON p.project_id = b.project_id
        Where b.project_id = {project_id}
        ORDER BY  b.perioada DESC
        FETCH FIRST 1 ROW ONLY""")
    for row in cursor:
        print(row)

def GetBugetDifferenceForProjects(project_id):
    cursor.execute(f"""SELECT 
    project_id,
    project_name,
    transaction_start,
    transaction_end,
    budget,
    LAG(budget) OVER (PARTITION BY project_id ORDER BY transaction_start) AS previous_budget,
    budget - LAG(budget) OVER (PARTITION BY project_id ORDER BY transaction_start) AS budget_change
FROM 
    Projects_History
WHERE 
    project_id = {project_id} AND ACTION <> 'DELETE'
ORDER BY 
    transaction_start""")
    for row in cursor:
        print(row)

def getStateAtMoment (time_moment):
    cursor.execute(f"""SELECT employee_id, name, position, action, transaction_start, transaction_end FROM Employees_History
Where Transaction_Start <= TO_DATE('{time_moment}', 'YYYY-MM-DD') AND (Transaction_End >= TO_DATE('{time_moment}', 'YYYY-MM-DD') OR Transaction_End IS NULL)
ORDER BY employee_id""")
    for row in cursor:
        print(row)

app = Flask(__name__)

# cursor.execute('SELECT * FROM Employees')
# for row in cursor:
#     print(row)
# print('------------------------------------------------')
#cursor.execute("INSERT into Employees (employee_id, name, position) VALUES (123, 'a', 'a2')")
# connection.commit();
#cursor.execute('SELECT * FROM Employees')
@app.route('/insert', methods=['POST'])
def insert():
    table = request.form['table']
    table_fields = []  # This will hold column names
    table_values = []  # This will hold user input values

    # Collect the column names (fields)
    for column in request.form:
        if column != 'table':  # Exclude the 'table' hidden field
            table_fields.append(column)
            table_values.append(request.form[column])  # Collect the value for each column

    # Call InsertIntoTable method with the collected data
    InsertIntoTable(table, table_fields, table_values)

    return redirect(url_for('home'))  # Redirect to home page after insert

@app.route('/', methods=['GET', 'POST'])
def home():
    # Connect to the Oracle database
    cursor = connection.cursor()

    selected_table = None
    table_data = {"columns": [], "rows": []}

    if request.method == 'POST':
        selected_table = request.form.get('table')
        if selected_table:
            table_data = SelectFromTable(selected_table, cursor)

    # List of tables for buttons
    table_names = [
        "Employees",
        "Employees_History",
        "Projects",
        "Projects_History",
        "Assignments",
        "Assignments_History"
    ]

    # Close the connection
    cursor.close()

    return render_template('index.html', table_names=table_names, table_data=table_data, selected_table=selected_table)


if __name__ == '__main__':
    app.run(debug=True)
    connection.close()
