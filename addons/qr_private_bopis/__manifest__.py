{
    'name': 'QR Private BOPIS',
    'version': '19.0.1.0.0',
    'category': 'Inventory',
    'summary': 'QR Code riêng cho khách hàng nhận hàng tại cửa hàng',
    'description': '''
        Module QR Private cho phép:
        - Tạo mã QR riêng cho mỗi đơn hàng
        - Gửi QR qua email cho khách hàng
        - Scan QR để xác thực và tự động validate picking
    ''',
    'author': 'Nguyên Khang',
    'depends': ['sale', 'stock', 'mail','sale_stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/stock_picking_views.xml',
        'views/qr_scanner_views.xml',
        'views/portal_templates.xml',
        'data/mail_template_data.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}