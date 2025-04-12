from datetime import datetime
from sqlalchemy import and_
from models import InventoryExtract


def find_replacement_extract(extract_name):
    """
    Find a replacement extract from inventory with the same name and earliest expiration date
    
    Args:
        extract_name (str): The name of the extract to replace
    
    Returns:
        InventoryExtract or None: The first matching extract from inventory, ordered by expiration date
    """
    today = datetime.now().date()
    
    # Find all available extracts with the same name that haven't expired
    available_extracts = InventoryExtract.query.filter(
        and_(
            InventoryExtract.name == extract_name,
            InventoryExtract.expiration_date >= today
        )
    ).order_by(InventoryExtract.expiration_date).first()
    
    return available_extracts
