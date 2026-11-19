# Copyright 2026 INVITU (<https://www.invitu.com>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class LoyaltyReward(models.Model):
    _inherit = "loyalty.reward"

    discount_attribute_value_ids = fields.Many2many(
        comodel_name="product.attribute.value",
        string="Discounted Attribute Values",
        help="If set, the discount only applies to the price extra of these "
        "values, one unit per reward claimed.",
    )
    discount_ptav_ids = fields.Many2many(
        comodel_name="product.template.attribute.value",
        compute="_compute_discount_ptav_ids",
    )

    @api.depends("discount_attribute_value_ids")
    def _compute_discount_ptav_ids(self):
        ptav_model = self.env["product.template.attribute.value"]
        for reward in self:
            if reward.discount_attribute_value_ids:
                reward.discount_ptav_ids = ptav_model.search(
                    [
                        (
                            "product_attribute_value_id",
                            "in",
                            reward.discount_attribute_value_ids.ids,
                        )
                    ]
                )
            else:
                reward.discount_ptav_ids = ptav_model

    @api.constrains("discount_attribute_value_ids", "discount_applicability")
    def _check_discount_attribute_value_applicability(self):
        for reward in self:
            if (
                reward.discount_attribute_value_ids
                and reward.discount_applicability == "cheapest"
            ):
                raise ValidationError(
                    self.env._(
                        "Discounted attribute values cannot be used on the "
                        "cheapest product."
                    )
                )
