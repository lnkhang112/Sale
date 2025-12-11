from odoo import models, fields, api, exceptions  # type: ignore
import json

class QrVerificationWizard(models.TransientModel):
    _name = 'qr_verification_wizard'
    _description = 'QR Code Verification Wizard'

    text = fields.Text(
        string='QR Code Data',
        required=True,
        help='Data extracted from the scanned QR code (paste JSON payload here for testing).'
    )

    def verify_qr_code(self):
        """Verify the QR code data and return a client notification action."""
        self.ensure_one()
        try:
            data = json.loads(self.text)
        except json.JSONDecodeError:
            raise exceptions.UserError(
                'Failed to decode QR code data. Please ensure it is valid JSON.'
            )

        token = data.get('qr_token')
        issued_at = data.get('qr_issued_at')  # optional: used for extra validation

        if not token:
            raise exceptions.UserError('Invalid QR code data: token missing.')

        sale_order = self.env['sale.order'].search([('qr_token', '=', token)], limit=1)
        if not sale_order:
            return self.notification_message(
                status=False,
                msg='No matching order found for the provided QR token.'
            )

        # Optionally verify issued_at matches stored issued timestamp (string equality)
        if issued_at:
            stored_issued_str = fields.Datetime.to_string(sale_order.qr_issued_at) if sale_order.qr_issued_at else None
            if stored_issued_str != issued_at:
                return self.notification_message(
                    status=False,
                    msg='QR issued timestamp does not match the order record.'
                )

        # Ensure current user is owner of the order (adjust logic as needed)
        if sale_order.partner_id and self.env.user.partner_id != sale_order.partner_id:
            return self.notification_message(
                status=False,
                msg='This QR code does not belong to your account.'
            )

        # Already used?
        if sale_order.qr_used_at:
            return self.notification_message(
                status=False,
                msg='This QR code has already been used.'
            )

        # Optionally check expiry
        if sale_order.qr_expires_at:
            now = fields.Datetime.now()
            if sale_order.qr_expires_at < now:
                return self.notification_message(
                    status=False,
                    msg='This QR code has expired.'
                )

        # Mark the QR code as used
        sale_order.write({'qr_used_at': fields.Datetime.now()})

        return self.notification_message(status=True)

    def notification_message(self, status, msg=None):
        """Return an action that shows a display_notification"""
        if status:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Validation Result",
                    "message": "Thank you — your QR code is valid.",
                    "type": "success",
                    "sticky": False,
                },
            }
        else:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Validation Result",
                    "message": f"Sorry, your QR code is invalid. {msg or ''}",
                    "type": "danger",
                    "sticky": False,
                },
            }
