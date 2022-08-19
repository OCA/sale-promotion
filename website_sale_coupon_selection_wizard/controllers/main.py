# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.http import request, route

from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleCouponWizard(WebsiteSale):
    @route(
        ["/promotions/<int:program_id>/apply"], type="http", auth="public", website=True
    )
    def promotion_program_apply(self, program_id, **kwargs):
        program = request.env["sale.coupon.program"].sudo().browse(program_id).exists()
        if not program or not program.active or not program.is_published:
            return
        # Prevent to apply a promotion to a processed order
        order = request.website.sale_get_order()
        if order and order.state != "draft":
            request.session["sale_order_id"] = None
            order = request.website.sale_get_order()
        # We won't apply it twice
        if program in (order.no_code_promo_program_ids | order.code_promo_program_id):
            return
        # If the promotion is directly applicable (promotion code), just apply without
        # further ado.
        if program.promo_code_usage == "code_needed" and (
            program not in order.sudo()._available_multi_criteria_multi_gift_programs()
        ):
            return self.pricelist(program.promo_code)
        # Let's inject some context into the view
        request.session["promotion_id"] = program.id
        return request.redirect("/shop/cart")

    @route()
    def pricelist(self, promo, **post):
        """When applying a configurable promotion code, we'll offer the customer
        to configure it."""
        if promo:
            order = request.website.sale_get_order()
            program = (
                request.env["sale.coupon.program"]
                .sudo()
                .search([("promo_code", "=", promo)])
            )
            if program in order.sudo()._available_multi_criteria_multi_gift_programs():
                request.session["promotion_id"] = program.id
                return request.redirect("/shop/cart")
        return super().pricelist(promo)

    @route()
    def cart(self, **post):
        response = super().cart(**post)
        promotion = request.session.get("promotion_id")
        if promotion:
            response.qcontext["promotion_id"] = (
                request.env["sale.coupon.program"].sudo().browse(promotion)
            )
        return response

    @route(["/promotions/dismiss"], type="http", auth="public", website=True)
    def promotion_in_cart_dismiss(self, **kw):
        request.session.pop("promotion_id", None)
        return request.redirect("/shop/cart")
