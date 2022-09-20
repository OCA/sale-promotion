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
            old_invoice_on_delivered = program.invoice_on_delivered
            program.invoice_on_delivered = (
                program.discount_line_product_id.invoice_policy == "delivery"
            )
            if old_invoice_on_delivered != program.invoice_on_delivered:
                program._assign_precise_uom_if_needed()

    @api.onchange("invoice_on_delivered")
    def _inverse_invoice_on_delivered(self):
        for rec in self:
            old_invoice_plolicy = rec.discount_line_product_id.invoice_policy
            rec.discount_line_product_id.invoice_policy = (
                "delivery" if rec.invoice_on_delivered else "order"
            )
            if rec.discount_line_product_id.invoice_policy != old_invoice_plolicy:
                rec._assign_precise_uom_if_needed()

    def _assign_precise_uom_if_needed(self):
        for program in self:
            if program.invoice_on_delivered:
                program.discount_line_product_id.uom_id = self.env.ref(
                    "sale_coupon_invoice_delivered.product_uom_precise_unit"
                )
            else:
                program.discount_line_product_id.uom_id = self.env.ref(
                    "uom.product_uom_unit"
                )
