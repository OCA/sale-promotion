from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers import main


class GiftCardController(main.WebsiteSale):

    @http.route('/shop/pay_with_gift_card', type='http', methods=['POST'], website=True, auth='public')
    def add_gift_card(self, gift_card_code, **post):
        gift_card = request.env["gift.card"].sudo().search([('code', '=', gift_card_code.strip())], limit=1)
        order = request.env['website'].get_current_website().sale_get_order()
        gift_card_status = order._pay_with_gift_card(gift_card)
        return request.redirect('/shop/payment' + '?keep_carrier=1' + ('&gift_card_error=%s' % gift_card_status if gift_card_status else ''))