from odoo import models, fields, api, exceptions  # type: ignore
import qrcode  # type: ignore
import io
import base64
import json
import secrets
class StockPicking(models.Model):
    _inherit = "stock.picking"

    qr_code = fields.Binary(
        string='QR Code',
        readonly=True,
        attachment=True,
        copy=False,
    )

    qr_token = fields.Char(
        string='QR Token',
        index=True,
        copy=False,
        size=128,
    )

    qr_issued_at = fields.Datetime(
        string='Issued At',
        index=True,
    )

    qr_expires_at = fields.Datetime(
        string='Expires At',
        index=True,
    )

    qr_used_at = fields.Datetime(
        string='Used At',
        index=True,
    )

    qr_version = fields.Integer(
        string='QR Version',
        default=1,
    )
    _sql_constraints = [
        ('unique_qr_token', 'unique(qr_token)', 'QR token must be unique.'),
    ]

    def _generate_unique_token(self, nbytes=16, max_attempts=5):
        """Generate token_urlsafe and ensure no local collision (best-effort)."""
        for _ in range(max_attempts):
            token = secrets.token_urlsafe(nbytes)
            if not self.search([('qr_token', '=', token)], limit=1):
                return token
        # fallback (extremely unlikely): return last token anyway — unique constraint will protect DB
        return secrets.token_urlsafe(nbytes)
    
    def action_confirm(self):
        res = super().action_confirm()
        # self._generate_qr_code()
        # return res
        for order in self:
            order._generate_qr_code()
        return res
    #

    def _generate_qr_code(self, ttl_seconds=None):
        """Generate QR code with order information after payment confirmation.
           Works for single record (ensure_one). Returns the created token.
        """
        self.ensure_one()

        # generate unique token (best-effort)
        token = self._generate_unique_token(16)
        datetime_now = fields.Datetime.now()
        # Prepare QR code data (extend as needed)
        qr_payload = {
            'qr_token': token,
            'qr_issued_at': fields.Datetime.to_string(datetime_now),
        }
        qr_string = json.dumps(qr_payload, ensure_ascii=False)

        # Build QR image
        qr = qrcode.QRCode(
            error_correction=qrcode.constants.ERROR_CORRECT_M,  # type: ignore
            box_size=10,
            border=4,
        )
        qr.add_data(qr_string)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        # Save image to bytes and base64-encode to string
        with io.BytesIO() as buffer:
            img.save(buffer, format="PNG")  # type: ignore
            qr_code_bytes = buffer.getvalue()

        qr_code_base64 = base64.b64encode(qr_code_bytes).decode('utf-8')

        self.write({
            'qr_code': qr_code_base64,
            'qr_token': token,
            'qr_issued_at': datetime_now,
            # 'qr_expires_at': expires,
            'qr_version': 1,
        })
        return token