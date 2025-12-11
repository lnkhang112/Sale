from odoo import http  #type: ignore
from odoo.http import request  #type: ignore
from odoo.addons.website_sale.controllers.main import WebsiteSale  #type: ignore
import logging

_logger = logging.getLogger(__name__)


class WebsiteSaleQR(WebsiteSale):

    @http.route('/shop/payment/validate',
                type='http',
                auth="public",
                website=True,
                sitemap=False)
    def shop_payment_validate(self, sale_order_id=None, **post):
        """Override to generate QR code after payment validation"""

        # Call parent method
        result = super(WebsiteSaleQR, self).shop_payment_validate(sale_order_id=sale_order_id, **post)

        # Get the order
        if sale_order_id is None:
            order = request.cart
            if not order and 'sale_last_order_id' in request.session:
                last_order_id = request.session['sale_last_order_id']
                order = request.env['sale.order'].sudo().browse(
                    last_order_id).exists()
        else:
            order = request.env['sale.order'].sudo().browse(sale_order_id)

        # Generate QR code if order exists and doesn't have one yet
        if order and not order.qr_code:
            tx_sudo = order.get_portal_last_transaction()

            # Only generate QR if payment is successful
            if tx_sudo and tx_sudo.state in ['done', 'authorized']:
                try:
                    order._generate_qr_code()
                except Exception:
                    _logger.exception("Failed to generate QR for order %s", order.id)

        return result

    @http.route(['/shop/confirmation'],
                type='http',
                auth="public",
                website=True,
                sitemap=False)
    def shop_payment_confirmation(self, **post):
        """Override to ensure QR code is available on confirmation page"""

        sale_order_id = request.session.get('sale_last_order_id')
        if sale_order_id:
            order = request.env['sale.order'].sudo().browse(sale_order_id)

            # Generate QR code if not exists
            if order.exists() and not order.qr_code:
                tx = order.get_portal_last_transaction()
                if tx and tx.state in ['done', 'authorized']:
                    try:
                        order._generate_qr_code()
                    except Exception:
                        _logger.exception("Failed to generate QR for order %s", order.id)

            values = self._prepare_shop_payment_confirmation_values(order)
            return request.render("website_sale.confirmation", values)

        return request.redirect(self._get_shop_path())
