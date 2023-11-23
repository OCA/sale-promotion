# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class LoyaltyCriteria(models.Model):
    _name = "loyalty.criteria"
    _description = "Loyalty Multi Product Criteria"

    rule_id = fields.Many2one(
        comodel_name="loyalty.rule",
    )
    rule_min_quantity = fields.Integer(
        string="Min. Quantity",
        compute="_compute_rule_min_quantity",
        store=True,
        readonly=True,
        help="Minimum required product quantity to get the reward",
    )
    product_ids = fields.Many2many(
        comodel_name="product.product",
        required=True,
    )

    @api.depends("product_ids")
    def _compute_rule_min_quantity(self):
        """Set the minimum quantity automatically to prevent errors"""
        for criteria in self.filtered(lambda x: x.product_ids):
            criteria.rule_min_quantity = len(criteria.product_ids)

    @api.constrains("rule_min_quantity")
    def _check_rule_min_qty(self):
        for criteria in self.filtered(lambda x: x.product_ids):
            if len(criteria.product_ids) != criteria.rule_min_quantity:
                raise ValidationError(
                    _(
                        "The minimum required product quantity to get the reward can't be"
                        "different from the number of products. Set the rule as repeatable"
                        "to avoid this constraint."
                    )
                )
