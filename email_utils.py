import os
from datetime import datetime, timedelta
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from models import InventoryExtract

def get_expiring_extracts(days_threshold=180):
    """
    Ottiene gli estratti in scadenza entro il numero di giorni specificato.
    
    Args:
        days_threshold (int): Numero di giorni prima della scadenza per considerare un estratto come "in scadenza"
    
    Returns:
        list: Lista di InventoryExtract in scadenza
    """
    threshold_date = datetime.now().date() + timedelta(days=days_threshold)
    return InventoryExtract.query.filter(
        InventoryExtract.expiration_date <= threshold_date
    ).order_by(InventoryExtract.expiration_date).all()

def send_expiration_notification(to_email, expiring_extracts, days_threshold):
    """
    Invia una notifica via email per gli estratti in scadenza.
    
    Args:
        to_email (str): Indirizzo email del destinatario
        expiring_extracts (list): Lista degli estratti in scadenza
        days_threshold (int): Soglia dei giorni utilizzata per il filtro
    
    Returns:
        bool: True se l'invio è avvenuto con successo, False altrimenti
    """
    # Verifica se è stata configurata la chiave API SendGrid
    sendgrid_key = os.environ.get('SENDGRID_API_KEY')
    if not sendgrid_key:
        return False, "Chiave API SendGrid non configurata"
    
    # Verifica se ci sono estratti in scadenza
    if not expiring_extracts:
        return False, "Nessun estratto in scadenza entro il periodo specificato"
    
    # Crea il messaggio email
    subject = f"Notifica: {len(expiring_extracts)} estratti allergici in scadenza entro {days_threshold} giorni"
    
    # Costruisce il contenuto HTML
    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            th, td {{ padding: 12px 15px; border-bottom: 1px solid #ddd; text-align: left; }}
            th {{ background-color: #f8f8f8; font-weight: bold; }}
            .header {{ background-color: #4b6cb7; color: white; padding: 20px; margin-bottom: 20px; }}
            .footer {{ background-color: #f8f8f8; padding: 20px; margin-top: 20px; font-size: 12px; }}
            .warning {{ color: #cc0000; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Notifica Estratti Allergici in Scadenza</h1>
        </div>
        
        <p>Gentile utente,</p>
        
        <p>Questo è un avviso automatico per informarLa che i seguenti estratti allergici scadranno entro <strong>{days_threshold} giorni</strong>.</p>
        
        <table>
            <tr>
                <th>Nome</th>
                <th>Tipo</th>
                <th>Lotto</th>
                <th>Produttore</th>
                <th>Data di Scadenza</th>
                <th>Giorni Rimanenti</th>
                <th>Quantità</th>
            </tr>
    """
    
    today = datetime.now().date()
    
    for extract in expiring_extracts:
        days_left = (extract.expiration_date - today).days
        warning_style = ' class="warning"' if days_left <= 180 else ''
        
        html_content += f"""
            <tr{warning_style}>
                <td>{extract.name}</td>
                <td>{extract.type}</td>
                <td>{extract.lot_number}</td>
                <td>{extract.manufacturer}</td>
                <td>{extract.expiration_date.strftime('%d/%m/%Y')}</td>
                <td>{days_left} giorni</td>
                <td>{extract.quantity}</td>
            </tr>
        """
    
    html_content += """
        </table>
        
        <p>Si raccomanda di pianificare la sostituzione degli estratti in scadenza per garantire la continuità del servizio.</p>
        
        <p>Cordiali saluti,<br>
        Sistema di Gestione Estratti Allergici</p>
        
        <div class="footer">
            <p>Questa è un'email automatica generata dal Sistema di Gestione Estratti Allergici. Si prega di non rispondere a questa email.</p>
        </div>
    </body>
    </html>
    """
    
    # Configura l'email
    message = Mail(
        from_email=Email("notifiche@gestioneallergeni.it"),
        to_emails=To(to_email),
        subject=subject
    )
    message.content = Content("text/html", html_content)
    
    # Invia l'email
    try:
        sg = SendGridAPIClient(sendgrid_key)
        sg.send(message)
        return True, f"Notifica inviata con successo a {to_email}"
    except Exception as e:
        return False, f"Errore nell'invio della notifica: {str(e)}"