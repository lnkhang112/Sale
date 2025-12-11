{
    'name': 'Website Sale Order QR Code',
    'category': 'Website',
    'summary': 'Generate QR codes for confirmed orders',
    'description': """
        Website Sale Order QR Code
        ===========================
        
        This module generates a QR code after payment confirmation containing:
        - Order token
        - Confirmation datetime
        
        The QR code is displayed on the confirmation page and can be used
        for order verification purposes.
    """,
    'author': 'Nguyen Cao Hoang',
    'depends': [
        'website',
				'website_sale',
        'sale_management',
        'point_of_sale',
    ],
    'external_dependencies': {
        'python': ['Pillow','qrcode'],
    },
    'data': [
        'views/website_sale_confirmation.xml',
        'views/sale_order_views.xml',
        'views/stock_picking_form.xml',
        'views/qr_verification_wizard_views.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}  #type: ignore
