from sqlalchemy import create_engine, text

try:
    engine = create_engine(
        "postgresql://postgres:admin123@localhost:5432/salesgenie"
    )

    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
        print("Database connected successfully!")

except Exception as error:
    print("Connection failed:", error)