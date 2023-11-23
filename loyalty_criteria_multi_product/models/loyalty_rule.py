# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class LoyaltyRule(models.Model):
    _inherit = "loyalty.rule"

    loyalty_criteria = fields.Selection(
        selection=[("domain", "Domain"), ("multi_product", "Multi Product")],
        string="Loyalty criteria",
        help="- Domain: Standard behavior. The products are evaluated by domain.\n"
        "- Multi product: rules can be applied to different products "
        "and all of the have to be fulfilled",
        default="domain",
    )
    loyalty_criteria_ids = fields.One2many(
        string="Multi Product Criterias",
        comodel_name="loyalty.criteria",
        inverse_name="rule_id",
    )

    @api.onchange("loyalty_criteria")
    def _onchange_loyalty_criteria(self):
        """Clear domain so we clear some other fields from the view"""
        if self.loyalty_criteria == "multi_product":
            self.product_domain = False
            self.product_ids = False
            self.product_category_id = False
            self.product_tag_id = False
