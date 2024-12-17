from flask import Flask, render_template, request, redirect, url_for, flash, session
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
    table_values_string=""
    for i in range(len(table_values)):
        table_values_string += f"{table_values[i]}, "
    table_values_string = table_values_string[:-2]
    # Create the insert command
    command = f"INSERT INTO {table} ({table_fields_string}) VALUES ({table_values_string})"
    print(command)
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
    # for row in cursor:
    #     print(row)
    rows = cursor.fetchall()  # Get all rows from the table
    columns = [desc[0] for desc in cursor.description]  # Get column names
    return {'columns': columns, 'rows': rows}

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
    rows = cursor.fetchall()  # Get all rows from the table
    columns = [desc[0] for desc in cursor.description]  # Get column names
    return {'columns': columns, 'rows': rows}

def getStateAtMoment (time_moment):
    cursor.execute(f"""SELECT employee_id, name, position, action, transaction_start, transaction_end FROM Employees_History
Where Transaction_Start <= TO_DATE('{time_moment}', 'YYYY-MM-DD') AND (Transaction_End >= TO_DATE('{time_moment}', 'YYYY-MM-DD') OR Transaction_End IS NULL)
ORDER BY employee_id""")
    rows = cursor.fetchall()  # Get all rows from the table
    columns = [desc[0] for desc in cursor.description]  # Get column names
    return {'columns': columns, 'rows': rows}

def format_date(value):
    # Ensure the date format is exactly 'YYYY-MM-DD' and return in TO_DATE format
    try:
        # Validate and reformat the date to match 'YYYY-MM-DD' format
        formatted_value = datetime.strptime(value, '%Y-%m-%d').strftime('%Y-%m-%d')
        return f"TO_DATE('{formatted_value}', 'YYYY-MM-DD')"
    except ValueError:
        raise ValueError(f"Invalid date format: {value}. Expected format is YYYY-MM-DD.")



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
            value = request.form[column]
            value = value.strip()  # Clean leading/trailing whitespace

            # Check if the field is a date field (fields prefixed with 'date_')
            if 'time' in column.lower():
                value = value.strip()  # Ensure no extra spaces
                if value:  # If the value is not empty, format it
                    formatted_value = f"TO_DATE('{value}', 'YYYY-MM-DD')"
                    table_values.append(formatted_value)  # Add TO_DATE directly for date fields
                else:
                    table_values.append('NULL')  # If no value, append NULL for date fields
            # Handle TO_DATE values (date-time values)
            elif value and len(value) == 19 and value[4] == '-' and value[7] == '-' and value[10] == ' ' and value[13] == ':' and value[16] == ':':
                formatted_value = f"TO_DATE('{value}', 'YYYY-MM-DD HH24:MI:SS')"
                table_values.append(formatted_value)  # Add TO_DATE directly for datetime
            # Handle integers
            elif value.isdigit():
                table_values.append(value)  # Append as-is for integers
            # Handle other strings (wrap in single quotes)
            else:
                table_values.append(f"'{value}'")  # Add single quotes for strings

            table_fields.append(column.replace('date_', '').replace('text_', ''))  # Add field name, removing prefix

    print("Table Fields:", table_fields)
    print("Table Values:", table_values)

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

    # Extract update fields and values
    update_fields, update_values = extract_update_fields_and_values(request.form)

    try:
        # Call the UpdateRow method to update the database
        UpdateRow(table, update_fields, update_values, row_name, row_id)
        flash('Row updated successfully!', 'success')
    except Exception as e:
        flash(f'Error updating row: {str(e)}', 'error')

    return redirect(url_for('home'))


def extract_update_fields_and_values(form_data):
    update_fields = []
    update_values = []

    # Loop through the form fields that start with 'update_'
    for key, value in form_data.items():
        if key.startswith('update_'):
            field_name = key.replace('update_', '')  # Extract field name
            update_fields.append(field_name)

            # Clean up value: Remove extra quotes
            value = value.strip().replace("'", "")


            # Process value based on type (date, timestamp, integer, or string)
            processed_value = process_value(value, field_name)
            update_values.append(processed_value)

    return update_fields, update_values


def process_value(value, field_name):
    # Check if it's a valid timestamp
    if is_valid_timestamp(value):
        return format_timestamp(value)
    # Check if it's a valid date (use "date" if your date fields are passed like that in the form)
    elif is_valid_date(value, field_name):
        return format_date(value)
    # If the value is numeric, convert it to an integer
    elif value.isdigit():
        return int(value)
    else:
        # Otherwise, treat it as a string and wrap in single quotes
        return f"'{value}'"


def format_timestamp(value):
    # Ensure the timestamp format is exactly 'YYYY-MM-DD HH:MM:SS' and return in TO_TIMESTAMP format
    try:
        # Validate and reformat the timestamp to match 'YYYY-MM-DD HH:MM:SS' format
        formatted_value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
        return f"TO_DATE('{formatted_value}', 'YYYY-MM-DD')"
    except ValueError:
        raise ValueError(f"Invalid timestamp format: {value}. Expected format is YYYY-MM-DD HH:MM:SS.")


def is_valid_date(value, field_name):
    # Check if the value matches a valid date format (YYYY-MM-DD)
    # You can modify this check to use a more complex field-based validation if needed
    try:
        datetime.strptime(value, '%Y-%m-%d')
        return True
    except ValueError:
        return False


def is_valid_timestamp(value):
    # Check if the value matches a timestamp format (YYYY-MM-DD HH:MM:SS)
    try:
        datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        return True
    except ValueError:
        return False

@app.route('/search', methods=['POST'])
def search():
    id_value = request.form.get('id_value')

    selected_table = request.form.get('selected_table')  # The selected table name
    if not selected_table:
        flash('No table selected.')
        return redirect(request.referrer)

    if not id_value.isdigit():  # Ensure the input is numeric
        flash('Please enter a valid numeric ID.')
        return redirect(request.referrer)
        #return render_template('index.html', selected_table="selected_table", table_data="", table_names=table_names)


    # Define ID columns for each table


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

@app.route('/top_budget', methods=['POST'])
def top_budget():
    project_id = request.form.get('project_id')

    if not project_id.isdigit():  # Ensure the input is numeric
        flash('Please enter a valid numeric ID.')
        return redirect(request.referrer)


    selected_table = request.form.get('selected_table')
    if not selected_table:
        flash('No table selected.')
        return redirect(request.referrer)

    table_names = [
        "Employees",
        "Employees_History",
        "Projects",
        "Projects_History",
        "Assignments",
        "Assignments_History"
    ]

    # Define the action based on the project_id
    if selected_table == 'Projects_History':
        try:
            # Fetch data using the provided function
            table_data = GetTopBugetForProject(project_id)
            if table_data['rows']:
                return render_template('index.html', selected_table=selected_table, table_data=table_data,table_names=table_names)
            else:
                flash(f'No results found for Project ID {project_id}.', 'warning')
        except Exception as e:
            flash(f"An error occurred: {e}", 'error')

        return redirect(url_for('home'))

@app.route('/state_emp', methods=['POST'])
def state_emp():
    emp_date = request.form['emp_date']  # '2024-07-01'
    print("Start Date:", emp_date)

    selected_table = request.form.get('selected_table')
    if not selected_table:
        flash('No table selected.')
        return redirect(request.referrer)

    table_names = [
        "Employees",
        "Employees_History",
        "Projects",
        "Projects_History",
        "Assignments",
        "Assignments_History"
    ]

    # Define the action based on the date
    if selected_table == 'Employees_History':
        try:
            # Fetch data using the provided function
            table_data = getStateAtMoment(emp_date)
            if table_data['rows']:
                return render_template('index.html', selected_table=selected_table, table_data=table_data,table_names=table_names)
            else:
                flash(f'No results found for date {emp_date}.', 'warning')
        except Exception as e:
            flash(f"An error occurred: {e}", 'error')

    return redirect(url_for('home'))

@app.route('/budget_diff', methods=['POST'])
def budget_diff():
    project_id = request.form.get('budget_diff_project_id')

    if not project_id.isdigit():  # Ensure the input is numeric
        flash('Please enter a valid numeric ID.')
        return redirect(request.referrer)

    selected_table = request.form.get('selected_table')
    if not selected_table:
        flash('No table selected.')
        return redirect(request.referrer)

    table_names = [
        "Employees",
        "Employees_History",
        "Projects",
        "Projects_History",
        "Assignments",
        "Assignments_History"
    ]

    # Define the action based on the project_id
    if selected_table == 'Projects_History':
        try:
            # Fetch data using the provided function
            table_data = GetBugetDifferenceForProjects(project_id)
            if table_data['rows']:
                return render_template('index.html', selected_table=selected_table, table_data=table_data,
                                       table_names=table_names)
            else:
                flash(f'No results found for Project ID {project_id}.', 'warning')
        except Exception as e:
            flash(f"An error occurred: {e}", 'error')

        return redirect(url_for('home'))


def perform_action_on_projects_history(action_value):
    # Your custom logic to perform action based on the action_value
    # For example, you might want to query something or update rows
    cursor.execute(f"SELECT * FROM Projects_History WHERE ACTION = '{action_value}'")
    rows = cursor.fetchall()

    if rows:
        return f"Found {len(rows)} records for action '{action_value}'"
    else:
        return f"No records found for action '{action_value}'"

if __name__ == '__main__':
    app.run(debug=True)
    connection.close()
