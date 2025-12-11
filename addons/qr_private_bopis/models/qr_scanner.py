from odoo import models, fields, api

class QRScanner(models.TransientModel):
    _name = 'qr.scanner'
    _description = 'QR Scanner Tool'
    
    scanned_token = fields.Char(string='Mã QR đã quét', required=True)
    result_message = fields.Text(string='Kết quả', readonly=True)
    result_success = fields.Boolean(string='Thành công', readonly=True)
    picking_id = fields.Many2one('stock.picking', string='Đơn hàng', readonly=True)
    
    def action_verify_qr(self):
        """Xác thực QR code"""
        self.ensure_one()
        
        # Extract token from URL if needed
        token = self.scanned_token
        if '/qr/verify/' in token:
            token = token.split('/qr/verify/')[-1]
        
        # Verify token
        picking_obj = self.env['stock.picking']
        result = picking_obj.verify_and_validate(token)
        
        self.result_success = result.get('success', False)
        self.result_message = result.get('message', 'Lỗi không xác định')
        
        if result.get('success'):
            picking = picking_obj.search([('qr_private_token', '=', token)], limit=1)
            self.picking_id = picking.id
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Thành công!',
                    'message': f"Đơn hàng {result.get('picking_name')} đã được xác nhận",
                    'type': 'success',
                    'sticky': False,
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Lỗi!',
                    'message': self.result_message,
                    'type': 'danger',
                    'sticky': True,
                }
            }