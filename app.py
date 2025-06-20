from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import date, datetime # Added datetime imports
from database_setup import create_table
import database_operations as db_ops # Use an alias for clarity

app = Flask(__name__)
app.secret_key = 'dev_secret_key' # For flash messages

# Initialize database table
# This ensures the table exists when the app starts.
# In a more complex app, you might use Flask-SQLAlchemy or Alembic for migrations.
create_table()
# Also, ensure the database_operations module uses the correct DB_FILE
# For this project structure, it's assumed database_operations.DB_FILE is "allergy_tracker.db"
# and database_setup.SETUP_DB_FILE is also "allergy_tracker.db" for non-test runs.

@app.route('/')
def index():
    """Displays the list of all allergenic extracts."""
    extracts = db_ops.get_all_extracts()
    return render_template('index.html', extracts=extracts)

@app.route('/add', methods=['GET', 'POST'])
def add_extract_route():
    """Handles adding a new allergenic extract."""
    if request.method == 'POST':
        name = request.form.get('name')
        batch_number = request.form.get('batch_number')
        expiry_date = request.form.get('expiry_date') if request.form.get('expiry_date') else None
        try:
            quantity_on_hand = int(request.form.get('quantity_on_hand'))
        except (ValueError, TypeError):
            flash('Invalid quantity. Please enter a number.', 'danger')
            return render_template('extract_form.html', form_title="Add New Extract", submit_button_text="Create Extract", extract=request.form)

        storage_location = request.form.get('storage_location')
        supplier_details = request.form.get('supplier_details')
        date_received = request.form.get('date_received') if request.form.get('date_received') else None
        notes = request.form.get('notes')

        if not name or quantity_on_hand is None: # Basic validation
            flash('Name and Quantity are required fields.', 'danger')
            # Pass current form data back to pre-fill the form
            return render_template('extract_form.html', form_title="Add New Extract", submit_button_text="Create Extract", extract=request.form)

        new_id = db_ops.add_extract(name, batch_number, expiry_date, quantity_on_hand,
                                   storage_location, supplier_details, date_received, notes)
        if new_id:
            flash(f"Extract '{name}' added successfully!", 'success')
        else:
            flash(f"Failed to add extract '{name}'.", 'danger')
        return redirect(url_for('index'))

    # GET request
    return render_template('extract_form.html', form_title="Add New Extract", submit_button_text="Create Extract")

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_extract_route(id):
    """Handles editing an existing allergenic extract."""
    extract = db_ops.get_extract_by_id(id)
    if not extract:
        flash(f"Extract with ID {id} not found.", 'warning')
        return redirect(url_for('index'))

    if request.method == 'POST':
        name = request.form.get('name')
        batch_number = request.form.get('batch_number')
        expiry_date = request.form.get('expiry_date') if request.form.get('expiry_date') else None
        try:
            quantity_on_hand = int(request.form.get('quantity_on_hand'))
        except (ValueError, TypeError):
            flash('Invalid quantity. Please enter a number.', 'danger')
            # Pass current form data and original extract back to pre-fill the form
            current_form_data = request.form.to_dict()
            current_form_data['id'] = id # ensure id is part of extract for template
            return render_template('extract_form.html', extract=current_form_data, form_title="Edit Extract", submit_button_text="Update Extract")


        storage_location = request.form.get('storage_location')
        supplier_details = request.form.get('supplier_details')
        date_received = request.form.get('date_received') if request.form.get('date_received') else None
        notes = request.form.get('notes')

        if not name or quantity_on_hand is None: # Basic validation
            flash('Name and Quantity are required fields.', 'danger')
            current_form_data = request.form.to_dict()
            current_form_data['id'] = id # ensure id is part of extract for template
            return render_template('extract_form.html', extract=current_form_data, form_title="Edit Extract", submit_button_text="Update Extract")

        success = db_ops.update_extract(id, name, batch_number, expiry_date, quantity_on_hand,
                                        storage_location, supplier_details, date_received, notes)
        if success:
            flash(f"Extract '{name}' (ID: {id}) updated successfully!", 'success')
        else:
            flash(f"Failed to update extract '{name}' (ID: {id}). No changes made or error occurred.", 'warning')
        return redirect(url_for('index'))

    # GET request - convert sqlite3.Row to a dict for easier template access if needed,
    # or ensure template handles Row objects (which it does via ['key'] access)
    return render_template('extract_form.html', extract=extract, form_title="Edit Extract", submit_button_text="Update Extract")

@app.route('/delete/<int:id>', methods=['POST'])
def delete_extract_route(id):
    """Handles deleting an allergenic extract."""
    extract = db_ops.get_extract_by_id(id) # Optional: check if extract exists before deleting for better feedback
    if not extract:
        flash(f"Extract with ID {id} not found. Could not delete.", 'warning')
        return redirect(url_for('index'))

    success = db_ops.delete_extract(id)
    if success:
        flash(f"Extract '{extract['name']}' (ID: {id}) deleted successfully.", 'success')
    else:
        flash(f"Failed to delete extract with ID {id}.", 'danger')
    return redirect(url_for('index'))

@app.route('/report/nearing_expiry', methods=['GET', 'POST'])
def report_nearing_expiry():
    days_threshold = 30 # Default value
    if request.method == 'POST':
        days_threshold = int(request.form.get('days_threshold', 30))

    raw_extracts = db_ops.get_extracts_nearing_expiry(days_threshold)
    extracts_with_days_left = []
    today = date.today()
    for extract_row in raw_extracts:
        extract = dict(extract_row)
        if extract.get('expiry_date'):
            try:
                expiry_dt = datetime.strptime(extract['expiry_date'], '%Y-%m-%d').date()
                extract['days_left'] = (expiry_dt - today).days
            except ValueError:
                extract['days_left'] = 'N/A (Invalid Date Format)'
        else:
            extract['days_left'] = 'N/A'
        extracts_with_days_left.append(extract)

    return render_template('report_nearing_expiry.html',
                           extracts=extracts_with_days_left,
                           days_threshold=days_threshold)

@app.route('/report/low_stock', methods=['GET', 'POST'])
def report_low_stock():
    quantity_threshold = 10 # Default value
    if request.method == 'POST':
        quantity_threshold = int(request.form.get('quantity_threshold', 10))

    extracts = db_ops.get_extracts_low_stock(quantity_threshold)
    return render_template('report_low_stock.html',
                           extracts=extracts,
                           quantity_threshold=quantity_threshold)

@app.route('/update_stock/<int:id>', methods=['POST'])
def update_stock_route(id):
    try:
        change_in_quantity = int(request.form.get('change_in_quantity'))
        success, value = db_ops.update_stock_quantity(id, change_in_quantity)
        if success:
            flash(f'Stock updated successfully. New quantity: {value}', 'success')
        else:
            flash(f'Failed to update stock. Current quantity unchanged: {value}', 'danger')
    except ValueError:
        flash('Invalid quantity change. Please enter a number.', 'danger')
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'danger')
    return redirect(url_for('index'))


if __name__ == '__main__':
    # It's good practice to ensure the DB_FILE in database_operations is set correctly
    # for non-test runs if it was changed for tests.
    # However, for this project, we assume they are consistently "allergy_tracker.db"
    # or handled by environment if more advanced.
    app.run(debug=True, host='0.0.0.0', port=5000)
