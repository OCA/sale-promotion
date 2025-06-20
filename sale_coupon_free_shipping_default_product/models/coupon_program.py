from odoo import api, models


class CouponProgram(models.Model):
    _inherit = "coupon.program"

    @api.model
    def create(self, vals):
        # avoids creating multiple products if a coupon program is duplicated
        if self.discount_line_product_id:
            vals["discount_line_product_id"] = self.discount_line_product_id.id
        if vals.get("reward_type") == "free_shipping":
            product = self.env.company.free_shipping_product_default
            if product:
                vals["discount_line_product_id"] = product.id
        program = super(CouponProgram, self).create(vals)

        return program
