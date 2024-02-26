# Copyright 2021 Tecnativa - David Vidal
# Copyright 2024 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.http import request, route

from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleLoyaltySuggestionWizard(WebsiteSale):
    def _get_sale_loyalty_reward_wizard(self, order, program):
        wizard = (
            request.env["sale.loyalty.reward.wizard"]
            .with_context(active_id=order.id)
            .sudo()
            .create({"selected_reward_id": program.reward_ids[:1].id})
        )
        return wizard.id

    @route(
        ["/promotions/<int:program_id>/apply"], type="http", auth="public", website=True
    )
    def promotion_program_apply(self, program_id, **kwargs):
        program = request.env["loyalty.program"].sudo().browse(program_id).exists()
        request.session.pop("wizard_id", None)
        if not program or not program.active or not program.is_published:
            return request.redirect("/shop/cart")
        # Prevent to apply a promotion to a processed order
        order = request.website.sale_get_order()
        if order and order.state != "draft":
            request.session["sale_order_id"] = None
            order = request.website.sale_get_order()
        # We won't apply it twice
        if program in order._get_reward_programs():
            return request.redirect("/shop/cart")
        wizard = self._get_sale_loyalty_reward_wizard(order, program)
        # Let's inject some context into the view
        request.session["promotion_id"] = program.id
        request.session["order_id"] = order.id
        request.session["wizard_id"] = wizard
        return request.redirect("/shop/cart")

    @route()
    def cart(self, **post):
        error = request.session.get("error_promo_code")
        response = super().cart(**post)
        promotion = request.session.get("promotion_id")
        order = request.session.get("sale_order_id")
        if promotion:
            program_id = request.env["loyalty.program"].sudo().browse(promotion)
            order_id = request.env["sale.order"].browse(order)
            wizard_id = request.session.get("wizard_id")
            wiz = request.env["sale.loyalty.reward.wizard"].browse(wizard_id)
            mandatory_program_options = wiz.loyalty_rule_line_ids
            response.qcontext["wizard_id"] = wizard_id
            response.qcontext["promotion_id"] = program_id
            response.qcontext["order_id"] = order_id
            response.qcontext["mandatory_program_options"] = mandatory_program_options
        if error:
            request.session["error_promo_code"] = error
        return response

    @route(["/promotions/dismiss"], type="http", auth="public", website=True)
    def promotion_in_cart_dismiss(self, **kw):
        request.session.pop("promotion_id", None)
        request.session.pop("error_promo_code", None)
        request.session.pop("wizard_id", None)
        return request.redirect("/shop/cart")
