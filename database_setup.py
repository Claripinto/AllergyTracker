import sqlite3

# Global variable for the database file
SETUP_DB_FILE = "allergy_tracker.db"

def create_table():
    """Creates the allergenic_extracts table in the database specified by SETUP_DB_FILE."""
    conn = None  # Initialize conn to None
    try:
        # Connect to the SQLite database using the global variable
        conn = sqlite3.connect(SETUP_DB_FILE)
        cursor = conn.cursor()

        # Define the SQL CREATE TABLE statement
        create_table_query = """
        CREATE TABLE IF NOT EXISTS allergenic_extracts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            batch_number TEXT,
            expiry_date DATE,
            quantity_on_hand INTEGER NOT NULL DEFAULT 0,
            storage_location TEXT,
            supplier_details TEXT,
            date_received DATE,
            notes TEXT
        );
        """

        # Execute the SQL statement
        cursor.execute(create_table_query)

        # Check if the table was created or already exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='allergenic_extracts';")
        table_exists = cursor.fetchone()

        if table_exists:
            print("Table 'allergenic_extracts' created successfully or already exists.")
        else:
            # This case should ideally not be reached if CREATE TABLE IF NOT EXISTS works as expected
            print("Error: Table 'allergenic_extracts' was not created.")


        # Commit the changes
        conn.commit()

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        # Close the database connection
        if conn:
            conn.close()

if __name__ == '__main__':
    create_table()
