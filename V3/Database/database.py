import sqlite3
import os

databaseFile = 'Program Files/database.db'

# Check if a file named "myfile.txt" exists in the current directory
if not os.path.exists(databaseFile):
    # Create the file if it does not exist
    with open(databaseFile, 'w') as f:
        pass

def create_table(table_name, columns):
    """
    Creates a table with the given name and columns in the database.

    Parameters:
    conn: A connection object to the database.
    table_name: The name of the table to be created.
    columns: A list of column names and data types, in the format "name data_type".
    """
    # Connect to the database
    conn = sqlite3.connect(databaseFile)
    cursor = conn.cursor()
    column_str = ", ".join(columns)
    cursor.execute(f"CREATE TABLE {table_name} ({column_str})")
    # Commit the changes to the database
    conn.commit()
    # Close the connection
    conn.close()

def insert_record(table_name, values):
    """
    Inserts a record into the given table.

    Parameters:
    conn: A connection object to the database.
    table_name: The name of the table to insert the record into.
    values: A list of values to be inserted, in the same order as the table's columns.
    """
    # Connect to the database
    conn = sqlite3.connect(databaseFile)
    cursor = conn.cursor()

    placeholders = ", ".join(["?"] * len(values))
    cursor.execute(f"INSERT INTO {table_name} VALUES ({placeholders})", values)
    # Commit the changes to the database
    conn.commit()
    # Close the connection
    conn.close()

def delete_table(table_name):
    """
    Deletes the given table from the database.

    Parameters:
    conn: A connection object to the database.
    table_name: The name of the table to delete.
    """
    # Connect to the database
    conn = sqlite3.connect(databaseFile)
    cursor = conn.cursor()
    # Execute command
    cursor.execute(f"DROP TABLE {table_name}")
    # Commit the changes to the database
    conn.commit()
    # Close the connection
    conn.close()

def select_all(table_name):
    """
    Retrieves all records from the given table.
    conn: A connection object to the database.
    table_name: The name of the table to retrieve records from.
    
    Returns:
    A list of tuples, where each tuple represents a record in the table.
    """
    # Connect to the database
    conn = sqlite3.connect(databaseFile)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    column_names = [column[0] for column in cursor.description]
    all = [dict(zip(column_names, record)) for record in cursor.fetchall()]
    # Close the connection
    conn.close()
    return all

def select_by_value(table_name, column, value):
    """
    Retrieves records from the given table by a specific column value.
    
    Parameters:
    conn: A connection object to the database.
    table_name: The name of the table to retrieve the records from.
    column: The name of the column to search for.
    value: The value of the column to search for.
    
    Returns:
    A list of tuples representing the retrieved records.
    """
    conn = sqlite3.connect(databaseFile)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name} WHERE {column}=?", (value,))
    column_names = [column[0] for column in cursor.description]
    data = [dict(zip(column_names, record)) for record in cursor.fetchall()]
    conn.close()
    return data

def select_by_id(table_name, id):
    """
    Retrieves a single record from the given table by its id column.
    conn: A connection object to the database.
    table_name: The name of the table to retrieve the record from.
    id: The value of the id column to search for.
    
    Returns:
    A tuple representing the record with the matching id.
    """
    # Connect to the database
    conn = sqlite3.connect(databaseFile)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name} WHERE id=?", (id,))
    column_names = [column[0] for column in cursor.description]
    data = [dict(zip(column_names, record)) for record in cursor.fetchall()]
    # Close the connection
    conn.close()
    return data

def update_by_id(table_name, id, columns, values):
    """
    Updates a single record in the given table by its id column.
    
    Parameters:
    conn: A connection object to the database.
    table_name: The name of the table to update the record in.
    id: The value of the id column to search for.
    columns: A list of column names to be updated.
    values: A list of new values to be set for the columns, in the same order as the columns list.
    """
    # Connect to the database
    conn = sqlite3.connect(databaseFile)
    cursor = conn.cursor()
    placeholders = ", ".join([f"{column}=?" for column in columns])
    cursor.execute(f"UPDATE {table_name} SET {placeholders} WHERE id=?", (*values, id))
    # Commit the changes to the database
    conn.commit()
    # Close the connection
    conn.close()

def update_by_value(table_name, where_column, where_value, columns, values):
    """
    Updates a single record in the given table by a specified column.
    
    Parameters:
    conn: A connection object to the database.
    table_name: The name of the table to update the record in.
    where_column: The name of the column to search for the where_value.
    where_value: The value to search for in the where_column.
    columns: A list of column names to be updated.
    values: A list of new values to be set for the columns, in the same order as the columns list.
    """
    # Connect to the database
    conn = sqlite3.connect(databaseFile)
    cursor = conn.cursor()
    placeholders = ", ".join([f"{column}=?" for column in columns])
    cursor.execute(f"UPDATE {table_name} SET {placeholders} WHERE {where_column}=?", (*values, where_value))
    # Commit the changes to the database
    conn.commit()
    # Close the connection
    conn.close()

def delete_record_by_value(table_name, column, value):
    """
    Deletes a single record from the given table by a specific column value.
    
    Parameters:
    conn: A connection object to the database.
    table_name: The name of the table to delete the record from.
    column: The name of the column to search for.
    value: The value of the column to search for.
    """
    # Connect to the database
    conn = sqlite3.connect(databaseFile)
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {table_name} WHERE {column}=?", (value,))
    # Commit the changes to the database
    conn.commit()
    # Close the connection
    conn.close()

def delete_record_by_id(table_name, id):
    """
    Deletes a single record from the given table by its id column.
    
    Parameters:
    conn: A connection object to the database.
    table_name: The name of the table to delete the record from.
    id: The value of the id column to search for.
    """
    # Connect to the database
    conn = sqlite3.connect(databaseFile)
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {table_name} WHERE id=?", (id,))
    # Commit the changes to the database
    conn.commit()
    # Close the connection
    conn.close()