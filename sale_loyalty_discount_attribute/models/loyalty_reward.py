from odoo import fields, models


class LoyaltyReward(models.Model):
    _inherit = "loyalty.reward"

    limit_discounted_attributes = fields.Selection(
        [
            ("disabled", ""),
            ("list_price", "On List Price and Attributes"),
            ("attributes", "On Attributes Only"),
        ],
        default="disabled",
    )
    discount_attribute_ids = fields.Many2many(
        "product.attribute", string="Discounted Attributes"
    )
