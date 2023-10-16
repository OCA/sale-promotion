# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class LoyaltyProgram(models.Model):
    _inherit = "loyalty.program"

    loyalty_criteria = fields.Selection(
        selection=[("domain", "Domain"), ("multi_product", "Multi Product")],
        string="Loyalty criteria",
        help="- Domain: Standard behavior. The products are evaluated by domain.\n"
        "- Multi product: different rules can be applied to different products "
        "and all of the have to be fulfilled",
        default="domain",
    )
    loyalty_criteria_ids = fields.One2many(
        string="Multi Product Criterias",
        comodel_name="loyalty.criteria",
        inverse_name="program_id",
    )

    # @api.onchange("loyalty_criteria")
    # def _onchange_loyalty_criteria(self):
    #     """Clear domain so we clear some other fields from the view"""
    #     if self.loyalty_criteria == "multi_product":
    #         self.rule_products_domain = False

    def _get_valid_products_multi_product(self, products, criteria):
        """Return valid products depending on the criteria repeat product setting. Then
        the main method will check if the minimum quantities are acomplished."""
        if criteria.repeat_product:
            return products.browse(
                [x.id for x in criteria.product_ids if x in products]
            )
        if not all([x in products for x in criteria.product_ids]):
            return self.env["product.product"]
        return criteria.product_ids
