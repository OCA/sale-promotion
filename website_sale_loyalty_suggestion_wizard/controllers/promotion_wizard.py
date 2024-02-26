# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.exceptions import ValidationError
from odoo.http import request, route

from odoo.addons.website_sale_loyalty.controllers.main import WebsiteSale


class WebsiteSaleLoyaltySuggestionWizardController(WebsiteSale):
    def _process_promotion_lines(self, wizard_id, promotion_lines):
        for product, qty in promotion_lines.items():
            line = wizard_id.loyalty_rule_line_ids.filtered(
                lambda x: x.product_id.id == int(product)
            )
            if len(promotion_lines) == 1:
                qty = line.units_required - line.units_included
            if not qty:
                continue
            line.units_to_include = qty

    def _process_reward_line_options(self, wizard_id, reward_line_options):
        reward_id = wizard_id.selected_reward_id
        if reward_id.reward_type == "product":
            reward_products = reward_id.reward_product_ids
            if len(reward_products) == 1:
                wizard_id.selected_product_id = reward_products.id
            else:
                wizard_id.selected_product_id = (
                    int(reward_line_options.get("selected_product_ids", False)[0])
                    or wizard_id.selected_product_id.id
                )

    @route(
        "/website_sale_loyalty_suggestion_wizard/get_defaults",
        type="json",
        auth="public",
        methods=["POST"],
    )
    def get_default_products(self):
        program_id = (
            request.env["loyalty.program"]
            .sudo()
            .browse(request.session.get("promotion_id"))
        )
        order_id = request.env["sale.order"].browse(
            request.session.get("sale_order_id")
        )
        wiz = self._get_sale_loyalty_reward_wizard(order_id, program_id)
        return wiz.selected_product_id.ids

    @route(
        "/website_sale_loyalty_suggestion_wizard/apply",
        type="json",
        auth="public",
        methods=["POST"],
    )
    def apply_promotion_public(
        self, program_id, promotion_lines, reward_line_options, **kw
    ):
        """Frontend controller that wraps common methods and handles errors properly"""
        order_id = request.env["sale.order"].browse(
            request.session.get("sale_order_id")
        )
        program_id = request.env["loyalty.program"].sudo().browse(program_id)
        wiz = self._get_sale_loyalty_reward_wizard(order_id, program_id)
        reward_id = reward_line_options.get("reward_id", False)
        wiz.selected_reward_id = int(reward_id) or (
            program_id.reward_ids.id if len(program_id.reward_ids) == 1 else False
        )
        if wiz.selected_reward_id:
            self._process_promotion_lines(wiz, promotion_lines)
            self._process_reward_line_options(wiz, reward_line_options)
        try:
            wiz.action_apply()
        except ValidationError as e:
            request.session["error_promo_code"] = str(e)
            return
        request.session.pop("promotion_id", None)
        request.session.pop("error_promo_code", None)
