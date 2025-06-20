import datetime
from database_operations import (
    add_extract,
    get_all_extracts,
    get_extract_by_id,
    update_extract,
    delete_extract,
    update_stock_quantity,
    get_extracts_nearing_expiry,
    get_extracts_low_stock
)
from database_setup import create_table

def get_date_input(prompt, current_value=None):
    """Prompts the user for a date (YYYY-MM-DD).
    Loops until a valid date is entered or the user enters nothing (for optional dates).
    Returns a date string or None.
    If current_value is provided, pressing Enter will keep it.
    """
    while True:
        if current_value:
            user_input = input(f"{prompt} (YYYY-MM-DD, current: {current_value}, press Enter to keep): ").strip()
            if not user_input:
                return current_value
        else:
            user_input = input(f"{prompt} (YYYY-MM-DD, press Enter to skip): ").strip()
            if not user_input:
                return None

        try:
            datetime.datetime.strptime(user_input, "%Y-%m-%d")
            return user_input
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD or leave blank if allowed.")

def get_int_input(prompt, current_value=None, required=False):
    """Prompts the user for an integer.
    Loops until a valid integer is entered or the user enters nothing (if not required).
    If current_value is provided, pressing Enter will keep it.
    """
    while True:
        if current_value is not None: # Check for None explicitly, as 0 is a valid int
            user_input = input(f"{prompt} (current: {current_value}, press Enter to keep): ").strip()
            if not user_input:
                return current_value
        else:
            user_input = input(f"{prompt}: ").strip()
            if not user_input and not required:
                return None
            if not user_input and required:
                print("This field is required.")
                continue

        try:
            return int(user_input)
        except ValueError:
            print("Invalid input. Please enter a whole number.")


def cli_add_extract():
    """Handles adding a new extract via CLI."""
    print("\n--- Add New Allergenic Extract ---")
    name = ""
    while not name:
        name = input("Name (required): ").strip()
        if not name:
            print("Name cannot be empty.")

    batch_number = input("Batch Number: ").strip() or None
    expiry_date = get_date_input("Expiry Date")

    quantity_on_hand = None
    while quantity_on_hand is None:
        try:
            quantity_str = input("Quantity on Hand (required, integer): ").strip()
            if not quantity_str:
                print("Quantity cannot be empty.")
                continue
            quantity_on_hand = int(quantity_str)
        except ValueError:
            print("Invalid quantity. Please enter a whole number.")

    storage_location = input("Storage Location: ").strip() or None
    supplier_details = input("Supplier Details: ").strip() or None
    date_received = get_date_input("Date Received")
    notes = input("Notes: ").strip() or None

    new_id = add_extract(name, batch_number, expiry_date, quantity_on_hand,
                         storage_location, supplier_details, date_received, notes)
    if new_id:
        print(f"Extract '{name}' added successfully with ID: {new_id}.")
    else:
        print(f"Failed to add extract '{name}'. Check logs for details.")

def cli_view_all_extracts():
    """Handles viewing all extracts via CLI."""
    print("\n--- All Allergenic Extracts ---")
    extracts = get_all_extracts()
    if not extracts:
        print("No allergenic extracts found in the database.")
        return

    # Print table header
    print(f"{'ID':<5} | {'Name':<30} | {'Batch No.':<15} | {'Expiry Date':<12} | {'Qty':<5} | {'Location':<20}")
    print("-" * 95)
    for extract in extracts:
        print(f"{extract['id']:<5} | {extract['name']:<30} | "
              f"{extract['batch_number'] or 'N/A':<15} | {extract['expiry_date'] or 'N/A':<12} | "
              f"{extract['quantity_on_hand']:<5} | {extract['storage_location'] or 'N/A':<20}")
    print("-" * 95)
    if extracts:
        print(f"Total: {len(extracts)} extracts.")

def cli_view_extract_details():
    """Handles viewing details of a specific extract via CLI."""
    print("\n--- View Extract Details ---")
    extract_id_str = input("Enter ID of the extract to view: ").strip()
    try:
        extract_id = int(extract_id_str)
    except ValueError:
        print("Invalid ID format. Please enter a number.")
        return

    extract = get_extract_by_id(extract_id)
    if extract:
        print("\n--- Extract Details ---")
        print(f"ID:                 {extract['id']}")
        print(f"Name:               {extract['name']}")
        print(f"Batch Number:       {extract['batch_number'] or 'N/A'}")
        print(f"Expiry Date:        {extract['expiry_date'] or 'N/A'}")
        print(f"Quantity on Hand:   {extract['quantity_on_hand']}")
        print(f"Storage Location:   {extract['storage_location'] or 'N/A'}")
        print(f"Supplier Details:   {extract['supplier_details'] or 'N/A'}")
        print(f"Date Received:      {extract['date_received'] or 'N/A'}")
        print(f"Notes:              {extract['notes'] or 'N/A'}")
        print("-------------------------")
    else:
        print(f"No extract found with ID {extract_id}.")

def cli_update_extract():
    """Handles updating an existing extract via CLI."""
    print("\n--- Update Allergenic Extract ---")
    extract_id_str = input("Enter ID of the extract to update: ").strip()
    try:
        extract_id = int(extract_id_str)
    except ValueError:
        print("Invalid ID format. Please enter a number.")
        return

    current_extract = get_extract_by_id(extract_id)
    if not current_extract:
        print(f"No extract found with ID {extract_id}.")
        return

    print("\n--- Current Extract Details (press Enter to keep current value) ---")
    print(f"ID: {current_extract['id']}")

    name = input(f"Name (current: {current_extract['name']}): ").strip() or current_extract['name']
    if not name: # Name is mandatory
        print("Name cannot be empty. Update aborted.")
        return

    batch_number = input(f"Batch Number (current: {current_extract['batch_number'] or 'N/A'}): ").strip() or current_extract['batch_number']
    expiry_date = get_date_input("Expiry Date", current_value=current_extract['expiry_date'])

    quantity_on_hand_str = input(f"Quantity on Hand (current: {current_extract['quantity_on_hand']}): ").strip()
    if quantity_on_hand_str:
        try:
            quantity_on_hand = int(quantity_on_hand_str)
        except ValueError:
            print("Invalid quantity. Using current value.")
            quantity_on_hand = current_extract['quantity_on_hand']
    else:
        quantity_on_hand = current_extract['quantity_on_hand']


    storage_location = input(f"Storage Location (current: {current_extract['storage_location'] or 'N/A'}): ").strip() or current_extract['storage_location']
    supplier_details = input(f"Supplier Details (current: {current_extract['supplier_details'] or 'N/A'}): ").strip() or current_extract['supplier_details']
    date_received = get_date_input("Date Received", current_value=current_extract['date_received'])
    notes = input(f"Notes (current: {current_extract['notes'] or 'N/A'}): ").strip() or current_extract['notes']

    if update_extract(extract_id, name, batch_number, expiry_date, quantity_on_hand,
                      storage_location, supplier_details, date_received, notes):
        print(f"Extract ID {extract_id} updated successfully.")
    else:
        print(f"Failed to update extract ID {extract_id}. Check logs or if data was unchanged.")

def cli_delete_extract():
    """Handles deleting an extract via CLI."""
    print("\n--- Delete Allergenic Extract ---")
    extract_id_str = input("Enter ID of the extract to delete: ").strip()
    try:
        extract_id = int(extract_id_str)
    except ValueError:
        print("Invalid ID format. Please enter a number.")
        return

    extract = get_extract_by_id(extract_id)
    if not extract:
        print(f"No extract found with ID {extract_id}.")
        return

    print("\n--- Extract to be Deleted ---")
    print(f"ID:           {extract['id']}")
    print(f"Name:         {extract['name']}")
    print(f"Batch Number: {extract['batch_number'] or 'N/A'}")
    print("-----------------------------")

    confirm = input("Are you sure you want to delete this extract? (y/n): ").strip().lower()
    if confirm == 'y':
        if delete_extract(extract_id):
            print(f"Extract ID {extract_id} deleted successfully.")
        else:
            print(f"Failed to delete extract ID {extract_id}. Check logs.")
    else:
        print("Deletion cancelled.")

# --- Inventory Management CLI Functions ---

def cli_update_stock():
    """Handles updating stock quantity (Receive/Dispense) via CLI."""
    print("\n--- Update Stock Quantity ---")
    extract_id = get_int_input("Enter ID of the extract to update stock for", required=True)
    if extract_id is None: return # User cancelled or invalid input handled by get_int_input

    extract = get_extract_by_id(extract_id)
    if not extract:
        print(f"No extract found with ID {extract_id}.")
        return

    print(f"\nCurrent details for '{extract['name']}' (ID: {extract['id']}):")
    print(f"Current Quantity on Hand: {extract['quantity_on_hand']}")

    change_in_quantity = get_int_input("Enter change in quantity (e.g., 20 to receive, -5 to dispense)", required=True)
    if change_in_quantity is None: return # User cancelled or invalid input

    success, new_quantity = update_stock_quantity(extract_id, change_in_quantity)

    if success:
        print(f"Stock quantity updated successfully. New quantity on hand: {new_quantity}")
    else:
        print(f"Failed to update stock quantity. Current quantity remains: {new_quantity}.")
        if new_quantity + change_in_quantity < 0 : # Check if it failed due to going negative
             print("This might be because the change would result in a negative stock level.")


def cli_view_nearing_expiry():
    """Handles listing extracts nearing expiry via CLI."""
    print("\n--- View Extracts Nearing Expiry ---")
    days_str = input("Show items expiring in how many days? (default 30, press Enter for default): ").strip()
    if not days_str:
        days_threshold = 30
    else:
        try:
            days_threshold = int(days_str)
            if days_threshold <= 0:
                print("Days threshold must be a positive number.")
                return
        except ValueError:
            print("Invalid input for days. Using default (30).")
            days_threshold = 30

    print(f"Searching for extracts expiring in the next {days_threshold} days...")
    extracts = get_extracts_nearing_expiry(days_threshold)

    if not extracts:
        print(f"No extracts found nearing expiry within the next {days_threshold} days.")
        return

    print(f"\n--- Extracts Nearing Expiry (within {days_threshold} days) ---")
    print(f"{'ID':<5} | {'Name':<30} | {'Expiry Date':<12} | {'Qty':<5} | {'Days Left':<10}")
    print("-" * 70)
    today = datetime.date.today()
    for extract in extracts:
        expiry_dt = datetime.datetime.strptime(extract['expiry_date'], "%Y-%m-%d").date()
        days_left = (expiry_dt - today).days
        print(f"{extract['id']:<5} | {extract['name']:<30} | {extract['expiry_date']:<12} | "
              f"{extract['quantity_on_hand']:<5} | {days_left if days_left >= 0 else 'Expired':<10}")
    print("-" * 70)
    print(f"Total: {len(extracts)} extracts nearing expiry.")


def cli_view_low_stock():
    """Handles listing low stock extracts via CLI."""
    print("\n--- View Low Stock Extracts ---")
    qty_str = input("Show items with stock at or below what quantity? (default 10, press Enter for default): ").strip()
    if not qty_str:
        quantity_threshold = 10
    else:
        try:
            quantity_threshold = int(qty_str)
            if quantity_threshold < 0: # Allow 0 as a threshold
                print("Quantity threshold cannot be negative.")
                return
        except ValueError:
            print("Invalid input for quantity. Using default (10).")
            quantity_threshold = 10

    print(f"Searching for extracts with stock at or below {quantity_threshold} units...")
    extracts = get_extracts_low_stock(quantity_threshold)

    if not extracts:
        print(f"No extracts found with stock at or below {quantity_threshold} units.")
        return

    print(f"\n--- Low Stock Extracts (<= {quantity_threshold} units) ---")
    print(f"{'ID':<5} | {'Name':<30} | {'Quantity on Hand':<20}")
    print("-" * 60)
    for extract in extracts:
        print(f"{extract['id']:<5} | {extract['name']:<30} | {extract['quantity_on_hand']:<20}")
    print("-" * 60)
    print(f"Total: {len(extracts)} extracts with low stock.")


def main_menu():
    """Displays the main menu and handles user choices."""
    # Ensure DB and table exist at startup
    try:
        print("Initializing database...")
        create_table()
        print("Database ready.")
    except Exception as e:
        print(f"Error initializing database: {e}")
        print("Please ensure database_setup.py and database_operations.py are present and configured.")
        return # Exit if DB setup fails

    while True:
        print("\n--- Allergenic Extract Management ---")
        print("1. Add Extract")
        print("2. View All Extracts")
        print("3. View Extract Details")
        print("4. Update Extract Details") # Renamed for clarity
        print("5. Delete Extract")
        print("--- Inventory ---")
        print("6. Update Stock Quantity")
        print("7. View Extracts Nearing Expiry")
        print("8. View Low Stock Extracts")
        print("9. Exit")

        choice = input("Enter your choice (1-9): ").strip()

        if choice == '1':
            cli_add_extract()
        elif choice == '2':
            cli_view_all_extracts()
        elif choice == '3':
            cli_view_extract_details()
        elif choice == '4':
            cli_update_extract()
        elif choice == '5':
            cli_delete_extract()
        elif choice == '6':
            cli_update_stock()
        elif choice == '7':
            cli_view_nearing_expiry()
        elif choice == '8':
            cli_view_low_stock()
        elif choice == '9':
            print("Exiting application. Goodbye!")
            break
        else:
            print("Invalid choice. Please enter a number between 1 and 9.")

        input("\nPress Enter to continue...")


if __name__ == '__main__':
    main_menu()
