from odoo import fields, models


class CouponReward(models.Model):
    _inherit = "coupon.reward"

    discount_line_product_id = fields.Many2one(
        "product.product",
        copy=True,
    )
