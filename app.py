import psycopg2
import requests
import json
import sys
import re

sys.stdout.reconfigure(encoding="utf-8")

GROQ_API_KEY = "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"
if not GROQ_API_KEY:
    raise ValueError("❌ Groq API Key not found. Set it as an environment variable.")
else:
    print("✅ Groq API Key loaded successfully!")

model_url = "https://api.groq.com/openai/v1/models"
headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}

response = requests.get(model_url, headers=headers)
if response.status_code == 200:
    available_models = response.json()
    print("\n✅ Available Models:", json.dumps(available_models, indent=2))
else:
    print(f"\n❌ Error fetching models: {response.status_code}, {response.text}")
    exit()

GROQ_MODEL = "mixtral-8x7b-32768"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

def query_groq(prompt):
    """Sends a prompt to the Groq API and returns the response."""
    payload = {
        "model": GROQ_MODEL, 
        "messages": [
            {"role": "system", "content": "You are an AI that corrects SQL queries. Only return the corrected SQL query without any explanation, markdown formatting, or additional text."},
            {"role": "user", "content": prompt}
        ], 
        "temperature": 0.5
    }

    response = requests.post(GROQ_API_URL, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
    else:
        raise Exception(f"Error: {response.status_code}, {response.text}")

def get_table_columns(conn, cursor, table_name):
    """Returns a list of column names for a given table."""
    try:
        cursor.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table_name}'")
        columns = [row[0] for row in cursor.fetchall()]
        return columns
    except Exception as e:
        print(f"❌ Error getting columns for table {table_name}: {str(e)}")
        return []

def get_available_tables(conn, cursor):
    """Returns a list of available tables in the database."""
    try:
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        tables = [row[0] for row in cursor.fetchall()]
        return tables
    except Exception as e:
        print(f"❌ Error getting available tables: {str(e)}")
        return []

def correct_sql(incorrect_sql, conn, cursor):
    """Uses Groq API to correct an incorrect SQL query and validates against database schema."""
    # First, get database schema information
    available_tables = get_available_tables(conn, cursor)
    print(f"\n✅ Available tables: {available_tables}")
    
    # Extract table name from the query (simplified approach)
    table_match = re.search(r'FROM\s+(\w+)', incorrect_sql, re.IGNORECASE)
    if table_match:
        table_name = table_match.group(1)
        if table_name not in available_tables:
            print(f"❌ Warning: Table '{table_name}' does not exist in the database.")
            # Add suggestion for available tables
            return None, f"Table '{table_name}' not found. Available tables: {available_tables}"
        
        # Get columns for the table
        columns = get_table_columns(conn, cursor, table_name)
        print(f"✅ Columns in {table_name}: {columns}")
        
        # Extract column names from the query
        column_matches = re.findall(r'SELECT\s+(?:SUM\((\w+)\)|(\w+))', incorrect_sql, re.IGNORECASE)
        column_names = []
        for match in column_matches:
            for group in match:
                if group and group != '':
                    column_names.append(group)
        
        for col in column_names:
            if col not in columns and col != '*':
                print(f"❌ Warning: Column '{col}' does not exist in table '{table_name}'.")
                return None, f"Column '{col}' not found in table '{table_name}'. Available columns: {columns}"
    
    # Get correction from Groq
    prompt = f"Fix this incorrect SQL query:\n{incorrect_sql}\nOnly provide the corrected SQL query, no explanations or markdown formatting."
    corrected_sql = query_groq(prompt)

    # Check if the corrected SQL is empty
    if not corrected_sql:
        return None, "❌ The corrected SQL query is empty."
    
    # Extract only the SQL query by removing any markdown code blocks
    corrected_sql = re.sub(r'```sql|```', '', corrected_sql).strip()
    
    # Try to find SQL keywords to ensure we're getting just the query
    sql_keywords = ["SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "ALTER", "DROP", "TRUNCATE"]
    for keyword in sql_keywords:
        if keyword in corrected_sql.upper():
            # Find the start of the SQL query
            start_index = corrected_sql.upper().find(keyword)
            if start_index != -1:
                corrected_sql = corrected_sql[start_index:]
                break
    
    # Remove any escape characters that might cause SQL syntax errors
    corrected_sql = corrected_sql.replace("\\_", "_").replace("\\-", "-")
    corrected_sql = corrected_sql.replace("\\", "")
    
    return corrected_sql, None

def connect_postgresql():
    """Returns a PostgreSQL connection and cursor."""
    try:
        conn = psycopg2.connect(
            dbname="postgres",
            user="postgres",
            password="diya123",
            host="localhost",
            port="5432"
        )
        return conn, conn.cursor()
    except Exception as e:
        print(f"❌ Error connecting to PostgreSQL: {str(e)}")
        return None, None

def execute_sql(conn, cursor, sql_query):
    """Executes the given SQL query on the PostgreSQL database."""
    try:
        # Print the exact query being executed for debugging
        print(f"Executing query: {sql_query}")
        
        cursor.execute(sql_query)
        # Check if the query is a SELECT query to fetch results
        if sql_query.strip().upper().startswith("SELECT"):
            result = cursor.fetchall()
        else:
            result = f"Query executed successfully. Rows affected: {cursor.rowcount}"
        conn.commit()
        return result
    except Exception as e:
        conn.rollback()  # Roll back in case of error
        return f"❌ Error executing SQL: {str(e)}"

# First, connect to PostgreSQL
conn, cursor = connect_postgresql()

if conn and cursor:
    # Get list of tables for suggestion
    available_tables = get_available_tables(conn, cursor)
    
    # For testing purposes, choose an available table
    if available_tables:
        sample_table = available_tables[0]
        columns = get_table_columns(conn, cursor, sample_table)
        
        if columns:
            # Create a sample query using actual table and column names
            sample_column = columns[0]
            sample_incorrect_sql = f"SELECT SUM({sample_column}) AS total_{sample_column} FROM {sample_table};"
        else:
            sample_incorrect_sql = "SELECT * FROM information_schema.tables LIMIT 5;"
    else:
        sample_incorrect_sql = "SELECT * FROM information_schema.tables LIMIT 5;"
    
    print(f"\n✅ Sample query based on your database: {sample_incorrect_sql}")
    
    # Get corrected SQL query
    corrected_sql, error_message = correct_sql(sample_incorrect_sql, conn, cursor)
    
    if error_message:
        print(f"\n❌ Validation Error: {error_message}")
    else:
        print("\n✅ Corrected SQL Query:\n", corrected_sql)
        
        # Execute the corrected SQL query
        query_result = execute_sql(conn, cursor, corrected_sql)
        print("\n✅ Query Result:\n", query_result)

    cursor.close()
    conn.close()
else:
    print("❌ Could not connect to PostgreSQL.")
