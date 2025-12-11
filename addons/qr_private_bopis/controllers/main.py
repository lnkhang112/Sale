from odoo import http
from odoo.http import request
import json
class QRVerifyController(http.Controller):
    
    @http.route('/qr/verify/<string:token>', type='http', auth='public', csrf=False)
    def verify_qr_token(self, token, **kwargs):
        """API endpoint để verify QR token"""
        picking_obj = request.env['stock.picking'].sudo()
        result = picking_obj.verify_and_validate(token)
        
        if result.get('success'):
            return request.render('qr_private_bopis.qr_verify_success', {
                'picking_name': result.get('picking_name'),
                'partner_name': result.get('partner_name'),
                'origin': result.get('origin')
            })
        else:
            return request.render('qr_private_bopis.qr_verify_error', {
                'error_message': result.get('message')
            })
    
    @http.route('/qr/verify/json/<string:token>', type='json', auth='public', csrf=False)
    def verify_qr_token_json(self, token):
        """API JSON để verify từ mobile app"""
        picking_obj = request.env['stock.picking'].sudo()
        return picking_obj.verify_and_validate(token)