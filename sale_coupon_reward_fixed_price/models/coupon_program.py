from odoo import api, models

from odoo.addons.coupon.models.coupon_program import (
    CouponProgram as CouponProgramOriginal,
)


class CouponProgram(models.Model):
    _inherit = "coupon.program"

    @api.model
    def create(self, vals):
        """
        Override method to ignore creation of `discount_line_product_id`
        if current program with reward type is `fixed_price`
        """
        if vals.get("reward_type") == "fixed_price":
            program = super(CouponProgramOriginal, self).create(vals)
        else:
            program = super(CouponProgram, self).create(vals)
        return program
