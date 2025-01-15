from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    free_shipping_product_default = fields.Many2one(
        comodel_name="product.product",
        string="Default promo product for free shipping",
        domain=[("detailed_type", "=", "service")],
        related="company_id.free_shipping_product_default",
        readonly=False,
    )
