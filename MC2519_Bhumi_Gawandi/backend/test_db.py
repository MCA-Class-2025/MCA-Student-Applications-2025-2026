from pymongo import MongoClient

uri = "mongodb+srv://expenseadmin:Expense12345@cluster0.okj5dsi.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

try:
    client = MongoClient(uri)

    client.admin.command("ping")

    print("✅ MongoDB Connected Successfully!")

    print("Databases:")
    print(client.list_database_names())

except Exception as e:
    print("❌ Connection Failed")
    print(e)