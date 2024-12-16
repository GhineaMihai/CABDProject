from flask import Flask, render_template, request, redirect, url_for, flash
import cx_Oracle
from datetime import datetime

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

def SelectRowFromTable(table, id_column, id_value):
    command = f'SELECT * FROM {table} WHERE {id_column} = {id_value}'
    cursor.execute(command)
    rows = cursor.fetchall()
    columns = [col[0] for col in cursor.description]  # Get column names
    return {"columns": columns, "rows": rows}

def InsertIntoTable(table, table_fields, table_values):
    table_fields_string = ", ".join(table_fields)  # Join field names
    table_values_string = ", ".join([f"'{value}'" for value in table_values])  # Join values and quote them

    # Create the insert command
    command = f"INSERT INTO {table} ({table_fields_string}) VALUES ({table_values_string})"
    cursor.execute(command)
    connection.commit()

def UpdateRow(table, update_fields, update_values, row_name, row_id):
    # Prepare the SET part of the SQL query
    table_update_fields = ""
    for i in range(len(update_fields)):
        table_update_fields += f"{update_fields[i]} = {update_values[i]}, "
    table_update_fields = table_update_fields[:-2]  # Remove trailing comma and space

    # Construct and execute the UPDATE command
    command = f"UPDATE {table} SET {table_update_fields} WHERE {row_name} = {row_id}"
    print(command)
    cursor.execute(command)
    connection.commit()

def DeleteRow(table, row_name, row_id):
    try:
        # Wrap row_id in quotes if it's a string to avoid SQL errors
        row_id_value = f"'{row_id}'" if isinstance(row_id, str) else row_id

        command = f"DELETE FROM {table} WHERE {row_name} = {row_id_value}"
        print(command)
        cursor.execute(command)
        connection.commit()
        return True  # Indicate success
    except Exception as e:
        print(f"Error deleting row: {e}")
        return False  # Indicate failure

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

def format_date(value):
    # Check if the value is in the format 'YYYY-MM-DD HH:MM:SS'
    try:
        # Try parsing the value into a datetime object with the format 'YYYY-MM-DD HH:MI:SS'
        datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        return f"TO_DATE('{value}', 'YYYY-MM-DD HH24:MI:SS')"  # Format for Oracle
    except ValueError:
        return value  # If not a valid date, return the value as is

def fetch_table_data(table):
    cursor.execute(f'SELECT * FROM {table}')
    rows = cursor.fetchall()  # Get all rows from the table
    columns = [desc[0] for desc in cursor.description]  # Get column names
    return {'columns': columns, 'rows': rows}

app = Flask(__name__)
app.secret_key = 'xddddd'

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

@app.route('/delete', methods=['POST'])
def delete():
    table = request.form['table']
    row_name = request.form['row_name']
    row_id = request.form['row_id']

    success = DeleteRow(table, row_name, row_id)

    if not success:
        flash(f"Failed to delete row with ID {row_id} from {table}.", "error")
    else:
        flash(f"Row with ID {row_id} successfully deleted from {table}.", "success")

    return redirect(url_for('home'))


@app.route('/update', methods=['POST'])
def update():
    table = request.form['table']
    row_name = request.form['row_name']
    row_id = request.form['row_id']

    update_fields = []
    update_values = []

    # Loop through the form fields that start with 'update_' and extract them
    for key, value in request.form.items():
        if key.startswith('update_'):  # All update fields are prefixed with 'update_'
            field_name = key.replace('update_', '')  # Extract field name
            update_fields.append(field_name)

            # Remove extra quotes from values if they exist
            value = value.replace("'", "")

            # If the value is a date, format it before appending
            if value and len(value) == 19 and value[4] == '-' and value[7] == '-' and value[10] == ' ' and value[
                13] == ':' and value[16] == ':':
                value = format_date(value)
                update_values.append(value)

            # If value is a number, convert it to an integer
            elif value.isdigit():
                update_values.append(int(value))
                continue
            else:
                # Otherwise, treat as a regular string
                update_values.append(f"'{value}'")

    try:
        # Call the UpdateRow method to update the database
        UpdateRow(table, update_fields, update_values, row_name, row_id)
        flash('Row updated successfully!', 'success')
    except Exception as e:
        flash(f'Error updating row: {str(e)}', 'error')

    return redirect(url_for('home'))


@app.route('/search', methods=['POST'])
def search():
    id_value = request.form.get('id_value')

    if not id_value.isdigit():  # Ensure the input is numeric
        flash('Please enter a valid numeric ID.')
        return redirect(request.referrer)

    selected_table = request.form.get('selected_table')  # The selected table name
    if not selected_table:
        flash('No table selected.')
        return redirect(request.referrer)

    # Define ID columns for each table
    id_columns = {
        'employees': 'EMPLOYEE_ID',
        'projects': 'PROJECT_ID',
        'assignments': 'ASSIGNMENT_ID',
        'employees_history': 'EMPLOYEE_ID',
        'projects_history': 'PROJECT_ID',
        'assignments_history': 'ASSIGNMENT_ID'
    }

    # List of tables for buttons
    table_names = [
        "Employees",
        "Employees_History",
        "Projects",
        "Projects_History",
        "Assignments",
        "Assignments_History"
    ]

    # Get the correct ID column based on the table
    id_column = id_columns.get(selected_table.lower())
    if not id_column:
        flash(f'No ID column found for table {selected_table}.')
        return redirect(request.referrer)

    # Fetch the search result data from the selected table
    table_data = SelectRowFromTable(selected_table, id_column, id_value)

    # Return the search result along with table data
    return render_template('index.html', selected_table=selected_table, table_data=table_data, table_names=table_names)

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
