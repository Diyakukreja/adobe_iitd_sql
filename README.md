# adobe_iitd_sql

# SQL Query Assistant

A powerful Python utility for correcting and executing SQL queries using Groq's LLM API and PostgreSQL.

## 📖 Overview

This tool provides a seamless way to correct SQL queries using Groq's language models and execute them against a PostgreSQL database. It can also convert natural language queries into SQL and execute them automatically.

## ✨ Features

- Automatically correct malformed or incorrect SQL queries
- Convert natural language requests into SQL 
- Connect to PostgreSQL database to execute queries
- Error handling for both API and database connections
- Support for schema context to improve query generation

## 🛠 Prerequisites

- Python 3.6+
- PostgreSQL database
- Groq API key

## 📦 Dependencies


pip install psycopg2 requests


## ⚙ Configuration

Before running the script, you need to:

1. Set up your Groq API key
2. Configure your PostgreSQL connection parameters

## 🚀 Getting Started

### Setting up your environment

1. Clone this repository
2. Install the required dependencies
3. Add your Groq API key to the script
4. Update the PostgreSQL connection parameters

### Basic Usage

python
# Correct an SQL query
incorrect_sql = "SELECT * FROM customerinfo JOIN wishlist ON customerinfo.person_customer_id = wishlist.priority_level"
corrected_sql = correct_sql(incorrect_sql)
print(corrected_sql)

# Execute the query against PostgreSQL
conn, cursor = connect_postgresql()
result = execute_sql(conn, cursor, corrected_sql)


### Natural Language to SQL

python
# Convert natural language to SQL and execute
nl_query = "Find the total revenue from sales in 2023"
schema_info = "Table: sales (id, product, amount, date)"
result = process_nl_query(nl_query, schema_info)


## 🔒 Security Notes

- Never commit your API keys to version control
- Consider using environment variables instead of hardcoding credentials
- Be cautious when running corrected SQL queries without review in production environments

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the issues page.

## 📝 License

[MIT License](LICENSE)

## 🙏 Acknowledgements

- [Groq](https://groq.com/) for their powerful LLM API
- [PostgreSQL](https://www.postgresql.org/) for the robust database system
