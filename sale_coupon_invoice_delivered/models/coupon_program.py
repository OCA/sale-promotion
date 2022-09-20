from odoo import api, fields, models


class CouponProgram(models.Model):
    _inherit = "coupon.program"

    invoice_on_delivered = fields.Boolean(
        string="Compute promotion on delivered quantities",
        compute="_compute_invoice_on_delivered",
        inverse="_inverse_invoice_on_delivered",
    )

    @api.depends("discount_line_product_id.invoice_policy")
    def _compute_invoice_on_delivered(self):
        for program in self:
            program.invoice_on_delivered = (
                program.discount_line_product_id.invoice_policy == "delivery"
            )

    @api.onchange("invoice_on_delivered")
    def _inverse_invoice_on_delivered(self):
        for rec in self:
            rec.discount_line_product_id.invoice_policy = (
                "delivery" if rec.invoice_on_delivered else "order"
            )
