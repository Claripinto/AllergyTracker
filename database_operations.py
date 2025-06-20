import sqlite3
import logging
from datetime import datetime, timedelta

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define the database file path
DB_FILE = "allergy_tracker.db"

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row  # To access columns by name
        return conn
    except sqlite3.Error as e:
        logging.error(f"Database connection error: {e}")
        raise  # Re-raise the exception if connection fails

def add_extract(name, batch_number, expiry_date, quantity_on_hand, storage_location, supplier_details, date_received, notes):
    """Adds a new allergenic extract to the database."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = """
        INSERT INTO allergenic_extracts
        (name, batch_number, expiry_date, quantity_on_hand, storage_location, supplier_details, date_received, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        cursor.execute(sql, (name, batch_number, expiry_date, quantity_on_hand, storage_location, supplier_details, date_received, notes))
        conn.commit()
        last_row_id = cursor.lastrowid
        logging.info(f"Extract '{name}' added successfully with ID: {last_row_id}.")
        return last_row_id
    except sqlite3.Error as e:
        logging.error(f"Error adding extract '{name}': {e}")
        return False
    except Exception as e:
        logging.error(f"An unexpected error occurred while adding extract '{name}': {e}")
        return False
    finally:
        if conn:
            conn.close()

def get_all_extracts():
    """Fetches all allergenic extracts from the database."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = "SELECT * FROM allergenic_extracts ORDER BY name;"
        cursor.execute(sql)
        extracts = cursor.fetchall()
        logging.info(f"Retrieved {len(extracts)} extracts from the database.")
        return extracts
    except sqlite3.Error as e:
        logging.error(f"Error fetching all extracts: {e}")
        return [] # Return empty list on error
    except Exception as e:
        logging.error(f"An unexpected error occurred while fetching all extracts: {e}")
        return []
    finally:
        if conn:
            conn.close()

def get_extract_by_id(extract_id):
    """Fetches a single allergenic extract by its ID."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = "SELECT * FROM allergenic_extracts WHERE id = ?;"
        cursor.execute(sql, (extract_id,))
        extract = cursor.fetchone()
        if extract:
            logging.info(f"Extract with ID {extract_id} retrieved successfully.")
        else:
            logging.info(f"No extract found with ID {extract_id}.")
        return extract
    except sqlite3.Error as e:
        logging.error(f"Error fetching extract with ID {extract_id}: {e}")
        return None # Return None on error
    except Exception as e:
        logging.error(f"An unexpected error occurred while fetching extract ID {extract_id}: {e}")
        return None
    finally:
        if conn:
            conn.close()

def update_extract(extract_id, name, batch_number, expiry_date, quantity_on_hand, storage_location, supplier_details, date_received, notes):
    """Updates an existing allergenic extract in the database."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = """
        UPDATE allergenic_extracts SET
        name = ?, batch_number = ?, expiry_date = ?, quantity_on_hand = ?,
        storage_location = ?, supplier_details = ?, date_received = ?, notes = ?
        WHERE id = ?;
        """
        cursor.execute(sql, (name, batch_number, expiry_date, quantity_on_hand, storage_location, supplier_details, date_received, notes, extract_id))
        conn.commit()
        if cursor.rowcount > 0:
            logging.info(f"Extract with ID {extract_id} updated successfully.")
            return True
        else:
            logging.warning(f"No extract found with ID {extract_id} to update, or data was the same.")
            return False # No rows affected, could mean ID not found or data is the same
    except sqlite3.Error as e:
        logging.error(f"Error updating extract with ID {extract_id}: {e}")
        return False
    except Exception as e:
        logging.error(f"An unexpected error occurred while updating extract ID {extract_id}: {e}")
        return False
    finally:
        if conn:
            conn.close()

def delete_extract(extract_id):
    """Deletes an allergenic extract from the database by its ID."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = "DELETE FROM allergenic_extracts WHERE id = ?;"
        cursor.execute(sql, (extract_id,))
        conn.commit()
        if cursor.rowcount > 0:
            logging.info(f"Extract with ID {extract_id} deleted successfully.")
            return True
        else:
            logging.warning(f"No extract found with ID {extract_id} to delete.")
            return False # No rows affected, likely ID not found
    except sqlite3.Error as e:
        logging.error(f"Error deleting extract with ID {extract_id}: {e}")
        return False
    except Exception as e:
        logging.error(f"An unexpected error occurred while deleting extract ID {extract_id}: {e}")
        return False
    finally:
        if conn:
            conn.close()

# --- Inventory Management Functions ---

def update_stock_quantity(extract_id, change_in_quantity):
    """Updates the stock quantity of an allergenic extract.
    Prevents quantity from going below zero.
    Returns (True, new_quantity) on success, or (False, current_quantity) on failure.
    """
    conn = None
    current_quantity = 0
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # First, get current quantity
        cursor.execute("SELECT quantity_on_hand FROM allergenic_extracts WHERE id = ?", (extract_id,))
        row = cursor.fetchone()

        if not row:
            logging.warning(f"update_stock_quantity: Extract ID {extract_id} not found.")
            return False, 0

        current_quantity = row['quantity_on_hand']
        new_quantity = current_quantity + change_in_quantity

        if new_quantity < 0:
            logging.warning(f"update_stock_quantity: Attempt to set negative stock for ID {extract_id}. Current: {current_quantity}, Change: {change_in_quantity}. Operation cancelled.")
            return False, current_quantity

        sql = "UPDATE allergenic_extracts SET quantity_on_hand = ? WHERE id = ?;"
        cursor.execute(sql, (new_quantity, extract_id))
        conn.commit()

        if cursor.rowcount > 0:
            logging.info(f"Stock quantity for extract ID {extract_id} updated from {current_quantity} to {new_quantity} (Change: {change_in_quantity}).")
            return True, new_quantity
        else:
            # Should not happen if ID was found initially, but good to have a fallback
            logging.error(f"update_stock_quantity: Failed to update stock for ID {extract_id}, though it was found. This is unexpected.")
            return False, current_quantity

    except sqlite3.Error as e:
        logging.error(f"Error updating stock for extract ID {extract_id}: {e}")
        return False, current_quantity
    except Exception as e:
        logging.error(f"An unexpected error occurred while updating stock for extract ID {extract_id}: {e}")
        return False, current_quantity
    finally:
        if conn:
            conn.close()

def get_extracts_nearing_expiry(days_threshold=30):
    """Fetches extracts nearing their expiry date."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        today_str = datetime.now().strftime("%Y-%m-%d")
        target_date_str = (datetime.now() + timedelta(days=days_threshold)).strftime("%Y-%m-%d")

        # Fetches extracts where expiry_date is not null, is after today, and is before or on the target date.
        sql = """
        SELECT * FROM allergenic_extracts
        WHERE expiry_date IS NOT NULL
          AND expiry_date > ?
          AND expiry_date <= ?
        ORDER BY expiry_date ASC;
        """
        cursor.execute(sql, (today_str, target_date_str))
        extracts = cursor.fetchall()
        logging.info(f"Retrieved {len(extracts)} extracts nearing expiry (within {days_threshold} days, expiring after {today_str} and by {target_date_str}).")
        return extracts
    except sqlite3.Error as e:
        logging.error(f"Error fetching extracts nearing expiry: {e}")
        return []
    except Exception as e:
        logging.error(f"An unexpected error occurred while fetching extracts nearing expiry: {e}")
        return []
    finally:
        if conn:
            conn.close()

def get_extracts_low_stock(quantity_threshold=10):
    """Fetches extracts with low stock quantity."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = "SELECT * FROM allergenic_extracts WHERE quantity_on_hand <= ? ORDER BY quantity_on_hand ASC;"
        cursor.execute(sql, (quantity_threshold,))
        extracts = cursor.fetchall()
        logging.info(f"Retrieved {len(extracts)} extracts with stock at or below {quantity_threshold}.")
        return extracts
    except sqlite3.Error as e:
        logging.error(f"Error fetching low stock extracts: {e}")
        return []
    except Exception as e:
        logging.error(f"An unexpected error occurred while fetching low stock extracts: {e}")
        return []
    finally:
        if conn:
            conn.close()


if __name__ == '__main__':
    # Example Usage (for testing purposes)
    logging.info("Running example usage for database_operations.py")


    # Ensure the database and table exist
    try:
        from database_setup import create_table
        logging.info("Ensuring database and table exist for example usage...")
        create_table() # This will print its own status message
    except ImportError:
        logging.error("database_setup.py not found. Cannot ensure table exists for examples.")
    except Exception as e:
        logging.error(f"Error during initial table setup for examples: {e}")

    logging.info("\n--- CRUD Examples ---")
    # Add a new extract for CRUD and inventory tests
    id1 = add_extract("Birch Pollen", "BP001", "2025-08-15", 50, "Fridge 1", "Supplier X", "2024-01-10", "Standard concentration")
    id2 = add_extract("Cat Dander", "CD002", (datetime.now() + timedelta(days=15)).strftime("%Y-%m-%d"), 5, "Fridge 2", "Supplier Y", "2024-02-01", "Special order")
    id3 = add_extract("Dust Mite", "DM003", (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d"), 25, "Shelf A", "Supplier Z", "2024-03-01", "High potency")
    add_extract("Timothy Grass", "TG004", "2024-07-01", 100, "Fridge 1", "Supplier X", "2023-07-01", "Expired but for testing `get_extracts_nearing_expiry` logic") # Expired
    add_extract("Short Ragweed", "SR005", (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"), 12, "Fridge 2", "Supplier Y", "2024-05-01", "Nearing expiry and low stock")


    if id1:
        logging.info(f"Added Birch Pollen with ID: {id1}")
    if id2:
        logging.info(f"Added Cat Dander with ID: {id2}")
    if id3:
        logging.info(f"Added Dust Mite with ID: {id3}")

    # View all
    all_extracts = get_all_extracts()
    logging.info(f"Total extracts: {len(all_extracts)}")
    # for ex in all_extracts:
    #     logging.info(f"  Ext: {dict(ex)}")


    logging.info("\n--- update_stock_quantity Examples ---")
    if id1:
        # Receive stock
        success, new_qty = update_stock_quantity(id1, 20) # 50 + 20 = 70
        if success:
            logging.info(f"ID {id1}: Received stock, new quantity: {new_qty}")

        # Dispense stock
        success, new_qty = update_stock_quantity(id1, -10) # 70 - 10 = 60
        if success:
            logging.info(f"ID {id1}: Dispensed stock, new quantity: {new_qty}")

        # Try to dispense more than available
        success, current_qty = update_stock_quantity(id1, -100) # Current is 60, try to dispense 100
        if not success:
            logging.info(f"ID {id1}: Failed to dispense more than available, current quantity remains: {current_qty}")

        # Check final quantity
        extract_check = get_extract_by_id(id1)
        if extract_check:
            logging.info(f"ID {id1}: Final quantity check: {extract_check['quantity_on_hand']}") # Should be 60

    # Test with non-existent ID
    success, qty = update_stock_quantity(9999, 10)
    if not success and qty == 0:
        logging.info("Correctly handled stock update for non-existent ID 9999.")


    logging.info("\n--- get_extracts_nearing_expiry Examples ---")
    # Default threshold (30 days)
    nearing_expiry_default = get_extracts_nearing_expiry()
    logging.info(f"Extracts nearing expiry (next 30 days): {len(nearing_expiry_default)}")
    for extract in nearing_expiry_default:
        logging.info(f"  ID: {extract['id']}, Name: {extract['name']}, Expires: {extract['expiry_date']}, Qty: {extract['quantity_on_hand']}")

    # Custom threshold (e.g., 7 days)
    nearing_expiry_custom = get_extracts_nearing_expiry(days_threshold=7)
    logging.info(f"Extracts nearing expiry (next 7 days): {len(nearing_expiry_custom)}")
    for extract in nearing_expiry_custom:
        logging.info(f"  ID: {extract['id']}, Name: {extract['name']}, Expires: {extract['expiry_date']}")


    logging.info("\n--- get_extracts_low_stock Examples ---")
    # Default threshold (10 units) - Cat Dander (ID2) should be 5, Short Ragweed (ID5) should be 12 (no),
    # Birch Pollen (ID1) is 60.
    # Let's update ID3 (Dust Mite) to have low stock
    if id3:
        update_extract(id3, "Dust Mite", "DM003", (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d"), 8, "Shelf A", "Supplier Z", "2024-03-01", "High potency - updated to low stock")

    low_stock_default = get_extracts_low_stock() # Cat Dander (5), Dust Mite (8)
    logging.info(f"Extracts with low stock (<= 10 units): {len(low_stock_default)}")
    for extract in low_stock_default:
        logging.info(f"  ID: {extract['id']}, Name: {extract['name']}, Quantity: {extract['quantity_on_hand']}")

    # Custom threshold (e.g., 20 units)
    # Short Ragweed (ID5) Qty is 12, so it should appear here.
    low_stock_custom = get_extracts_low_stock(quantity_threshold=20)
    logging.info(f"Extracts with low stock (<= 20 units): {len(low_stock_custom)}")
    for extract in low_stock_custom:
        logging.info(f"  ID: {extract['id']}, Name: {extract['name']}, Quantity: {extract['quantity_on_hand']}")


    # Clean up: Optionally delete test data
    # logging.info("\n--- Cleaning up test data ---")
    # if id1: delete_extract(id1)
    # if id2: delete_extract(id2)
    # if id3: delete_extract(id3)
    # delete_extract(get_extract_by_id(find_id_by_name_or_batch("TG004"))) # More robust way if IDs change
    # delete_extract(get_extract_by_id(find_id_by_name_or_batch("SR005")))


    logging.info("\n--- Example usage finished ---")
