# Copyright 2024 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.http import request, route

from odoo.addons.website_sale_loyalty.controllers.main import WebsiteSale


class WebsiteSaleLoyaltySuggestionWizardMultiProductController(WebsiteSale):
    @route()
    def cart(self, **post):
        response = super().cart(**post)
        promotion = request.session.get("promotion_id")
        if promotion:
            program_id = request.env["loyalty.program"].sudo().browse(promotion)
            if program_id.rule_ids.filtered(
                lambda x: x.loyalty_criteria == "multi_product"
            ):
                order_id = request.env["sale.order"].browse(
                    request.session.get("sale_order_id")
                )
                wizard_id = self._get_sale_loyalty_reward_wizard(order_id, program_id)
                product = next(
                    (
                        line.product_id
                        for line in order_id.order_line
                        if line.suggested_promotion_ids.filtered(
                            lambda x: x.is_published
                        )[:1].id
                        == 5
                    ),
                    None,
                )
                if not product:
                    # If there are no products in the shopping cart that match the rules
                    # of the promotion being configured since it is being applied from
                    # "/promotions", the first multi-product rule is searched for and
                    # the first product is set up to calculate the "loyalty_rule_line_ids
                    # in the wizard_id
                    product = wizard_id.selected_reward_id.program_id.rule_ids.filtered(
                        lambda x: x.loyalty_criteria == "multi_product"
                    )[:1].loyalty_criteria_ids.product_ids[:1]
                wizard_id.product_id = product.id
                wizard_id._compute_loyalty_rule_line_ids()
                # To use in _compute_loyalty_rule_line_ids when applying the
                # configured promotion
                request.session["multi_product_id"] = product.id
                mandatory_program_options = wizard_id.loyalty_rule_line_ids
                response.qcontext[
                    "mandatory_program_options"
                ] = mandatory_program_options
        return response
