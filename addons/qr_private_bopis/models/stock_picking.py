import secrets
import hashlib
from odoo import models, fields, api
from odoo.exceptions import UserError
import qrcode
import base64
from io import BytesIO
import logging

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    qr_private_token = fields.Char(
        string='QR Private Token',
        readonly=True,
        copy=False,
        help='Token bảo mật duy nhất cho đơn hàng này'
    )
    qr_private_code = fields.Binary(
        string='QR Code',
        readonly=True,
        attachment=True,
        copy=False
    )
    qr_token_sent = fields.Boolean(
        string='QR đã gửi',
        default=False,
        copy=False
    )
    is_bopis = fields.Boolean(
        string='Là đơn BOPIS',
        compute='_compute_is_bopis',
        store=True,
        help='Tự động xác định đơn hàng nhận tại cửa hàng'
    )
    
    @api.depends('picking_type_id', 'location_dest_id')
    def _compute_is_bopis(self):
        """Tự động xác định đơn BOPIS dựa trên picking type và location"""
        for picking in self:
            picking.is_bopis = picking._is_bopis_order()
    
    def _is_bopis_order(self):
        """Kiểm tra đơn hàng có phải BOPIS không"""
        self.ensure_one()
        
        # Kiểm tra qua Sale Order (nếu có module sale_stock)
        if 'sale_id' in self._fields and self.sale_id:
            if hasattr(self.sale_id, 'carrier_id') and self.sale_id.carrier_id:
                carrier_name = self.sale_id.carrier_id.name.lower()
                bopis_keywords = ['pickup', 'store', 'bopis', 'lấy tại', 'nhận tại', 'tại cửa hàng']
                if any(keyword in carrier_name for keyword in bopis_keywords):
                    return True
        
        # Kiểm tra qua Picking Type
        if self.picking_type_id:
            picking_type_name = self.picking_type_id.name.lower()
            if any(keyword in picking_type_name for keyword in ['pickup', 'bopis', 'customer pickup']):
                return True
        
        # Kiểm tra qua location
        if self.location_dest_id:
            location_name = self.location_dest_id.name.lower()
            if 'store' in location_name or 'pickup' in location_name:
                return True
        
        return False
    
    def generate_qr_token(self):
        """Tạo token bảo mật cho QR code - CHỈ CHO ĐƠN BOPIS"""
        for picking in self:
            # CHỈ TẠO QR CHO ĐƠN BOPIS
            if not picking.is_bopis:
                continue
                
            if not picking.qr_private_token:
                # Tạo token ngẫu nhiên an toàn
                random_token = secrets.token_urlsafe(32)
                # Hash với thông tin đơn hàng để tăng bảo mật
                token_string = f"{picking.id}-{picking.name}-{random_token}"
                picking.qr_private_token = hashlib.sha256(token_string.encode()).hexdigest()
                
                # Tạo QR code ngay sau khi có token
                picking._generate_qr_image()
                
                # TỰ ĐỘNG GỬI EMAIL - THÊM DÒNG NÀY
                picking._auto_send_qr_email()
        return True
    
    def _generate_qr_image(self):
        """Tạo hình ảnh QR code từ token"""
        for picking in self:
            if picking.qr_private_token:
                # Tạo URL verify với token
                base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                verify_url = f"{base_url}/qr/verify/{picking.qr_private_token}"
                
                # Tạo QR code
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(verify_url)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                
                # Convert sang binary
                buffer = BytesIO()
                img.save(buffer, format='PNG')
                picking.qr_private_code = base64.b64encode(buffer.getvalue())
    
    def _auto_send_qr_email(self):
        """Tự động gửi QR code qua email sau khi tạo"""
        self.ensure_one()
        
        # Kiểm tra đã gửi chưa
        if self.qr_token_sent:
            _logger.info(f"QR email đã gửi trước đó cho {self.name}")
            return
        
        # Kiểm tra có QR code chưa
        if not self.qr_private_code:
            _logger.warning(f"Chưa có QR code cho {self.name}")
            return
        
        # Kiểm tra có email khách hàng không
        if not self.partner_id or not self.partner_id.email:
            _logger.warning(f"Không có email khách hàng cho {self.name}")
            return
        
        # Gửi email
        try:
            template = self.env.ref('qr_private_bopis.email_template_qr_code', raise_if_not_found=False)
            if template:
                template.send_mail(self.id, force_send=True)
                self.qr_token_sent = True
                _logger.info(f"✅ Đã gửi QR email thành công cho {self.name} đến {self.partner_id.email}")
            else:
                _logger.warning(f"Không tìm thấy email template 'qr_private_bopis.email_template_qr_code'")
        except Exception as e:
            # Log lỗi nhưng không block flow
            _logger.error(f"❌ Lỗi gửi QR email cho {self.name}: {str(e)}")
    
    def action_confirm(self):
        """Override để tự động tạo QR cho đơn BOPIS khi confirm"""
        res = super().action_confirm()
        for picking in self:
            if picking.is_bopis:
                picking.generate_qr_token()
        return res
    
    def action_assign(self):
        """Override để tự động tạo QR khi assign (ready to pick)"""
        res = super().action_assign()
        for picking in self:
            if picking.is_bopis and not picking.qr_private_token:
                picking.generate_qr_token()
        return res
    
    def action_send_qr_email(self):
        """Gửi lại QR code qua email (manual trigger nếu cần)"""
        self.ensure_one()
        
        # Kiểm tra có phải đơn BOPIS không
        if not self.is_bopis:
            raise UserError('Chỉ gửi QR Code cho đơn hàng BOPIS (nhận tại cửa hàng).')
        
        # Tạo token nếu chưa có
        if not self.qr_private_token:
            self.generate_qr_token()
        
        # Force compute QR code để đảm bảo có hình
        self._generate_qr_image()
        
        # Kiểm tra QR code đã được tạo chưa
        if not self.qr_private_code:
            raise UserError('Không thể tạo QR Code. Vui lòng kiểm tra lại.')
        
        # Gửi email (force gửi lại)
        template = self.env.ref('qr_private_bopis.email_template_qr_code', raise_if_not_found=False)
        if template:
            template.send_mail(self.id, force_send=True)
            self.qr_token_sent = True
        else:
            raise UserError('Không tìm thấy template email. Vui lòng kiểm tra cấu hình.')
        
        return True
    
    def verify_and_validate(self, token):
        """Xác thực token và tự động validate picking"""
        picking = self.search([('qr_private_token', '=', token)], limit=1)
        if not picking:
            return {'success': False, 'message': 'Mã QR không hợp lệ'}
        
        # Kiểm tra có phải đơn BOPIS không
        if not picking.is_bopis:
            return {'success': False, 'message': 'Đây không phải đơn BOPIS'}
        
        if picking.state == 'done':
            return {'success': False, 'message': 'Đơn hàng đã được giao trước đó'}
        
        if picking.state != 'assigned':
            return {'success': False, 'message': f'Đơn hàng chưa sẵn sàng (Trạng thái: {picking.state})'}
        
        # Validate picking
        try:
            picking.button_validate()
            return {
                'success': True,
                'message': 'Xác nhận thành công',
                'picking_name': picking.name,
                'partner_name': picking.partner_id.name,
                'origin': picking.origin or ''
            }
        except Exception as e:
            return {'success': False, 'message': f'Lỗi: {str(e)}'}