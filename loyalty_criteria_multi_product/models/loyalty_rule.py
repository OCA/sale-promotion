# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import Command, api, fields, models


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

    def _get_multi_product_reset_values(self):
        return {
            "minimum_qty": 0.0,
            "minimum_amount": 0.0,
            "product_domain": False,
            "product_ids": [Command.clear()],
            "product_category_id": False,
            "product_tag_id": False,
        }

    @api.onchange("loyalty_criteria")
    def _onchange_loyalty_criteria(self):
        """Clear fields that do not apply to the selected criteria."""
        if self.loyalty_criteria == "multi_product":
            self.update(self._get_multi_product_reset_values())
        else:
            self.loyalty_criteria_ids = False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("loyalty_criteria") == "multi_product":
                vals.update(self._get_multi_product_reset_values())
        return super().create(vals_list)

    def write(self, vals):
        if vals.get("loyalty_criteria") == "multi_product":
            vals.update(self._get_multi_product_reset_values())
        return super().write(vals)
