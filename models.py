from datetime import datetime
from app import db


class Extract(db.Model):
    """Base extract model with common fields for both inventory and panels"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # inalante, alimentare, controllo
    lot_number = db.Column(db.String(50), nullable=False)
    manufacturer = db.Column(db.String(100), nullable=False)
    
    # Discriminator column for the inheritance
    extract_type = db.Column(db.String(20))
    
    __mapper_args__ = {
        'polymorphic_on': extract_type,
        'polymorphic_identity': 'extract'
    }
    
    def __repr__(self):
        return f"<Extract {self.name} - Lot: {self.lot_number}>"


class InventoryExtract(Extract):
    """Model for extracts in inventory"""
    __tablename__ = 'inventory_extract'
    
    id = db.Column(db.Integer, db.ForeignKey('extract.id'), primary_key=True)
    expiration_date = db.Column(db.Date, nullable=False)
    loading_date = db.Column(db.Date, nullable=False, default=datetime.now().date())
    quantity = db.Column(db.Integer, nullable=False, default=1)
    
    __mapper_args__ = {
        'polymorphic_identity': 'inventory',
    }
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'lot_number': self.lot_number,
            'manufacturer': self.manufacturer,
            'expiration_date': self.expiration_date.strftime('%Y-%m-%d') if self.expiration_date else None,
            'loading_date': self.loading_date.strftime('%Y-%m-%d') if self.loading_date else None,
            'quantity': self.quantity
        }


class PanelExtract(Extract):
    """Model for extracts in panels"""
    __tablename__ = 'panel_extract'
    
    id = db.Column(db.Integer, db.ForeignKey('extract.id'), primary_key=True)
    start_date = db.Column(db.Date, nullable=False, default=datetime.now().date())
    end_date = db.Column(db.Date, nullable=True)
    panel_id = db.Column(db.Integer, db.ForeignKey('panel.id'), nullable=False)
    
    __mapper_args__ = {
        'polymorphic_identity': 'panel',
    }
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'lot_number': self.lot_number,
            'manufacturer': self.manufacturer,
            'start_date': self.start_date.strftime('%Y-%m-%d') if self.start_date else None,
            'end_date': self.end_date.strftime('%Y-%m-%d') if self.end_date else None,
            'panel_id': self.panel_id
        }


class Panel(db.Model):
    """Model for panels that contain extracts"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    extracts = db.relationship('PanelExtract', backref='panel', lazy=True)
    
    def __repr__(self):
        return f"<Panel {self.name}>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'extracts': [extract.to_dict() for extract in self.extracts]
        }


class ExtractUsageHistory(db.Model):
    """Model for tracking extract usage history"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(20), nullable=False)
    lot_number = db.Column(db.String(50), nullable=False)
    manufacturer = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    panel_name = db.Column(db.String(50), nullable=False)
    
    def __repr__(self):
        return f"<ExtractUsageHistory {self.name} - Panel: {self.panel_name}>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'lot_number': self.lot_number,
            'manufacturer': self.manufacturer,
            'start_date': self.start_date.strftime('%Y-%m-%d') if self.start_date else None,
            'end_date': self.end_date.strftime('%Y-%m-%d') if self.end_date else None,
            'panel_name': self.panel_name
        }
