# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.http import request, route

from odoo.addons.website_sale_loyalty_page.controllers.main import WebsiteSale


class LoyaltyPage(WebsiteSale):
    @route()
    def promotion(self, **post):
        """Rules to render the 'Apply promotion' button"""
        response = super().promotion(**post)
        order = request.cart or request.website._create_cart()
        if not order:
            return response
        promo_values = response.qcontext.get("promos", [])
        for promo_dict in promo_values:
            promo_dict["applicable"] = False
            promo = request.env["loyalty.program"].sudo().browse(promo_dict["id"])
            if promo not in order.sudo()._filter_programs_by_rules_with_products():
                continue
            promo_dict["applicable"] = True
        return response
