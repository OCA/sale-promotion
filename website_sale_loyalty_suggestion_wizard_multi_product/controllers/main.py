# Copyright 2024 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.http import request, route

from odoo.addons.website_sale_loyalty.controllers.main import WebsiteSale


class WebsiteSaleLoyaltySuggestionWizardMultiProductController(WebsiteSale):
    @route()
    def cart(self, **post):
        promotion = request.session.get("promotion_id")
        order = request.session.get("sale_order_id")
        if promotion:
            program_id = request.env["loyalty.program"].sudo().browse(promotion)
            if program_id.rule_ids.filtered(
                lambda x: x.loyalty_criteria == "multi_product"
            ):
                wizard = request.env["sale.loyalty.reward.wizard"].browse(
                    request.session.get("wizard_id")
                )
                order = request.env["sale.order"].browse(
                    request.session.get("sale_order_id")
                )
                product = next(
                    (
                        line.product_id
                        for line in order.order_line
                        if line.suggested_promotion_ids.filtered(
                            lambda x: x.is_published
                        )[:1].id
                        == 5
                    ),
                    None,
                )
                if product:
                    wizard.product_id = product.id
                    wizard._compute_loyalty_rule_line_ids()
        return super().cart(**post)
