from datetime import datetime
import io
import csv
from flask import render_template, request, redirect, url_for, flash, jsonify, make_response
from sqlalchemy import extract as sql_extract

from app import app, db
from models import Panel, PanelExtract, InventoryExtract, ExtractUsageHistory
from utils import find_replacement_extract

# Helper function to use in templates to get current date
@app.context_processor
def inject_now():
    return {'now': datetime.now}


@app.route('/')
def home():
    """Homepage route"""
    panel_count = Panel.query.count()
    active_extracts = PanelExtract.query.filter_by(end_date=None).count()
    inventory_count = InventoryExtract.query.count()
    
    # Count extracts expiring in the next 30 days
    from datetime import timedelta
    today = datetime.now().date()
    # Use timedelta instead of day replacement to avoid issues with month boundaries
    thirty_days_later = today + timedelta(days=30)
    soon_expiring = InventoryExtract.query.filter(
        InventoryExtract.expiration_date >= today,
        InventoryExtract.expiration_date <= thirty_days_later
    ).count()
    
    return render_template('home.html', 
                           panel_count=panel_count,
                           active_extracts=active_extracts,
                           inventory_count=inventory_count,
                           soon_expiring=soon_expiring)


@app.route('/panels')
def panels():
    """List all panels with their extracts"""
    panels_data = Panel.query.all()
    return render_template('panels.html', panels=panels_data)


@app.route('/panels/add', methods=['POST'])
def add_panel():
    """Add a new panel"""
    name = request.form.get('name')
    description = request.form.get('description', '')
    
    if not name:
        flash('Il nome del pannello è obbligatorio', 'danger')
        return redirect(url_for('panels'))
    
    # Check if panel with this name already exists
    existing_panel = Panel.query.filter_by(name=name).first()
    if existing_panel:
        flash(f'Un pannello con il nome "{name}" esiste già', 'warning')
        return redirect(url_for('panels'))
    
    new_panel = Panel(name=name, description=description)
    db.session.add(new_panel)
    db.session.commit()
    
    flash(f'Pannello "{name}" aggiunto con successo', 'success')
    return redirect(url_for('panels'))


@app.route('/panels/delete/<int:panel_id>', methods=['POST'])
def delete_panel(panel_id):
    """Delete a panel and all its associated extracts"""
    panel = Panel.query.get_or_404(panel_id)
    panel_name = panel.name
    
    # Delete all associated extracts (this will also delete the panel due to cascading)
    PanelExtract.query.filter_by(panel_id=panel_id).delete()
    db.session.delete(panel)
    db.session.commit()
    
    flash(f'Pannello "{panel_name}" eliminato con successo', 'success')
    return redirect(url_for('panels'))


@app.route('/panels/<int:panel_id>')
def panel_detail(panel_id):
    """Show panel details with options to add extracts"""
    panel = Panel.query.get_or_404(panel_id)
    inventory_extracts = InventoryExtract.query.all()
    return render_template('panel_detail.html', panel=panel, inventory=inventory_extracts)


@app.route('/panels/<int:panel_id>/add_extract', methods=['POST'])
def add_extract_to_panel(panel_id):
    """Add an extract from inventory to a panel"""
    panel = Panel.query.get_or_404(panel_id)
    inventory_id = request.form.get('inventory_id')
    
    if not inventory_id:
        flash('Seleziona un estratto', 'danger')
        return redirect(url_for('panel_detail', panel_id=panel_id))
    
    # Get the extract from inventory
    inventory_extract = InventoryExtract.query.get_or_404(inventory_id)
    
    # Create a new panel extract
    panel_extract = PanelExtract(
        name=inventory_extract.name,
        type=inventory_extract.type,
        lot_number=inventory_extract.lot_number,
        manufacturer=inventory_extract.manufacturer,
        start_date=datetime.now().date(),
        panel_id=panel_id
    )
    
    # Add the extract to the panel and remove from inventory
    db.session.add(panel_extract)
    db.session.delete(inventory_extract)
    db.session.commit()
    
    flash(f'Estratto "{inventory_extract.name}" aggiunto al pannello', 'success')
    return redirect(url_for('panel_detail', panel_id=panel_id))


@app.route('/panels/extract/<int:extract_id>/close', methods=['POST'])
def close_extract(extract_id):
    """Close an extract and replace it with one from inventory if available"""
    extract = PanelExtract.query.get_or_404(extract_id)
    panel_id = extract.panel_id
    
    # Set the end date
    extract.end_date = datetime.now().date()
    
    # Add to usage history
    usage_history = ExtractUsageHistory(
        name=extract.name,
        type=extract.type,
        lot_number=extract.lot_number,
        manufacturer=extract.manufacturer,
        start_date=extract.start_date,
        end_date=extract.end_date,
        panel_name=extract.panel.name
    )
    db.session.add(usage_history)
    
    # Look for a replacement
    replacement = find_replacement_extract(extract.name)
    
    if replacement:
        # Create a new panel extract
        new_extract = PanelExtract(
            name=replacement.name,
            type=replacement.type,
            lot_number=replacement.lot_number,
            manufacturer=replacement.manufacturer,
            start_date=datetime.now().date(),
            panel_id=panel_id
        )
        
        # Add the new extract and remove from inventory
        db.session.add(new_extract)
        db.session.delete(replacement)
        
        flash(f'Estratto chiuso e sostituito con uno nuovo dall\'inventario', 'success')
    else:
        flash(f'Estratto chiuso. Nessun sostituto trovato nell\'inventario.', 'warning')
    
    db.session.commit()
    return redirect(url_for('panel_detail', panel_id=panel_id))


@app.route('/inventory')
def inventory():
    """List all extracts in inventory"""
    inventory_extracts = InventoryExtract.query.order_by(InventoryExtract.expiration_date).all()
    return render_template('inventory.html', inventory=inventory_extracts)


@app.route('/inventory/add', methods=['POST'])
def add_inventory():
    """Add new extracts to inventory, with support for multiple items of the same lot number"""
    name = request.form.get('name')
    extract_type = request.form.get('type')
    lot_number = request.form.get('lot_number')
    manufacturer = request.form.get('manufacturer')
    expiration_date = request.form.get('expiration_date')
    
    # Get quantity field (default to 1 if not provided)
    try:
        quantity = int(request.form.get('quantity', 1))
        if quantity < 1:
            quantity = 1  # Ensure at least one extract is added
    except ValueError:
        quantity = 1
    
    # Validate inputs
    if not all([name, extract_type, lot_number, manufacturer, expiration_date]):
        flash('Tutti i campi sono obbligatori', 'danger')
        return redirect(url_for('inventory'))
    
    try:
        exp_date = datetime.strptime(expiration_date, '%Y-%m-%d').date()
    except ValueError:
        flash('Formato data di scadenza non valido. Usa AAAA-MM-GG', 'danger')
        return redirect(url_for('inventory'))
    
    # Add the specified number of extracts
    for i in range(quantity):
        # Create new inventory extract
        new_extract = InventoryExtract(
            name=name,
            type=extract_type,
            lot_number=lot_number,
            manufacturer=manufacturer,
            expiration_date=exp_date
        )
        db.session.add(new_extract)
    
    db.session.commit()
    
    if quantity == 1:
        flash(f'Estratto "{name}" aggiunto all\'inventario', 'success')
    else:
        flash(f'{quantity} estratti "{name}" aggiunti all\'inventario', 'success')
    
    return redirect(url_for('inventory'))


@app.route('/reports')
def reports():
    """Report generation page"""
    current_year = datetime.now().year
    years = list(range(current_year - 5, current_year + 1))
    return render_template('reports.html', years=years)


@app.route('/reports/generate', methods=['POST'])
def generate_report():
    """Generate a report for a specific year"""
    year = request.form.get('year')
    if not year:
        flash('Seleziona un anno', 'danger')
        return redirect(url_for('reports'))
    
    try:
        year = int(year)
    except ValueError:
        flash('Formato anno non valido', 'danger')
        return redirect(url_for('reports'))
    
    # Get all extracts used in the specified year
    extracts = ExtractUsageHistory.query.filter(
        sql_extract('year', ExtractUsageHistory.start_date) == year
    ).order_by(ExtractUsageHistory.start_date).all()
    
    if not extracts:
        flash(f'Nessun estratto utilizzato nel {year}', 'warning')
        return redirect(url_for('reports'))
    
    # Generate CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Nome', 'Tipo', 'Numero Lotto', 'Produttore', 'Data Inizio', 'Data Fine', 'Pannello'])
    
    # Write data
    for extract in extracts:
        writer.writerow([
            extract.name,
            extract.type,
            extract.lot_number,
            extract.manufacturer,
            extract.start_date.strftime('%d/%m/%Y'),
            extract.end_date.strftime('%d/%m/%Y') if extract.end_date else 'Ancora in uso',
            extract.panel_name
        ])
    
    # Create response
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = f"attachment; filename=report_estratti_{year}.csv"
    response.headers["Content-type"] = "text/csv"
    
    return response


@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404


@app.route('/inventory/delete/<int:extract_id>', methods=['POST'])
def delete_inventory_extract(extract_id):
    """Delete an extract from inventory"""
    extract = InventoryExtract.query.get_or_404(extract_id)
    extract_name = extract.name
    
    db.session.delete(extract)
    db.session.commit()
    
    flash(f'Estratto "{extract_name}" eliminato dall\'inventario', 'success')
    return redirect(url_for('inventory'))


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
