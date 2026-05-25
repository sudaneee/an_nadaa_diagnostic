import qrcode
from io import BytesIO
from django.core.files import File
from django.conf import settings
import os

def generate_invoice_qr(invoice):
    """Generate QR code for invoice"""
    qr_data = f"""
    An-Nadaa Diagnostic Centre
    Invoice: {invoice.invoice_number}
    Client: {invoice.client.full_name}
    Phone: {invoice.client.phone_number}
    Amount: ₦{invoice.total_amount}
    Status: {invoice.get_status_display()}
    """
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save to BytesIO
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    
    # Save to file
    filename = f'qr_{invoice.invoice_number}.png'
    filepath = os.path.join('qr_codes', filename)
    
    if not os.path.exists(os.path.join(settings.MEDIA_ROOT, 'qr_codes')):
        os.makedirs(os.path.join(settings.MEDIA_ROOT, 'qr_codes'))
    
    with open(os.path.join(settings.MEDIA_ROOT, filepath), 'wb') as f:
        f.write(buffer.getvalue())
    
    return filepath