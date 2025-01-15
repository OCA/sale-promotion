from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    free_shipping_product_default = fields.Many2one(
        "product.product", string="Default promo product for free shipping"
    )
