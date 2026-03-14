from backend.llm.sql_generator import generate_sql
from backend.services.query_executor import execute_query


query = "Show top 5 videos by views"

print("\nUser Query:")
print(query)

sql = generate_sql(query)

print("\nGenerated SQL:")
print(sql)

data = execute_query(sql)

print("\nQuery Result:")
for row in data:
    print(row)