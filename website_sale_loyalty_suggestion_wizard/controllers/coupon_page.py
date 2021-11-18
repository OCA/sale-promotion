# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.http import request, route

from odoo.addons.website_sale_coupon_page.controllers.main import WebsiteSale


class CouponPage(WebsiteSale):
    @route()
    def promotion(self, **post):
        """Rules to render the 'Apply promotion' button"""
        response = super().promotion(**post)
        order = request.website.sale_get_order(force_create=True)
        if not order:
            return response
        promo_values = response.qcontext.get("promos", [])
        for promo_dict in promo_values:
            promo_dict["applicable"] = False
            promo = request.env["sale.coupon.program"].sudo().browse(promo_dict["id"])
            if (
                promo in (order.no_code_promo_program_ids | order.code_promo_program_id)
            ) or (
                promo
                not in order.sudo()._available_multi_criteria_multi_gift_programs()
            ):
                continue
            promo_dict["applicable"] = True
        return response
