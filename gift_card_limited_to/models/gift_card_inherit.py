from odoo import fields, models

class GiftCardCustom(models.Model):
    _inherit = "gift.card"

    limited_to_product_id = fields.Many2one('product.template', string="Limited to")