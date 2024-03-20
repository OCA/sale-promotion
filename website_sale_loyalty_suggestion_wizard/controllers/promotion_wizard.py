# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.exceptions import ValidationError
from odoo.http import request, route

from odoo.addons.website_sale_loyalty.controllers.main import WebsiteSale


class WebsiteSaleLoyaltySuggestionWizardController(WebsiteSale):
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
        program = request.env["loyalty.program"].sudo().browse(program_id)
        wizard_id = request.session.get("wizard_id")
        wiz = request.env["sale.loyalty.reward.wizard"].sudo().browse(wizard_id)
        reward_id = reward_line_options.get("reward", False)
        wiz.selected_reward_id = int(reward_id) or (
            program.reward_ids.id if len(program.reward_ids) == 1 else False
        )
        if wiz.selected_reward_id:
            reward = wiz.selected_reward_id
            for product, qty in promotion_lines.items():
                line = wiz.loyalty_rule_line_ids.filtered(
                    lambda x: x.product_id.id == int(product)
                )
                if len(promotion_lines) == 1:
                    qty = line.units_required - line.units_included
                if not qty:
                    continue
                line.units_to_include = qty
            if reward.reward_type == "product":
                reward_products = reward.reward_product_ids
                if len(reward_products) == 1:
                    wiz.selected_product_id = reward_products.id
                else:
                    wiz.selected_product_id = int(
                        reward_line_options.get("reward_product")
                    )
        try:
            wiz.action_apply()
        except ValidationError as e:
            request.session["error_promo_code"] = str(e)
            return
        request.session.pop("promotion_id", None)
        request.session.pop("error_promo_code", None)
        request.session.pop("wizard_id", None)
