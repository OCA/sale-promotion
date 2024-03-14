from odoo import fields, models

class ProductTemplateCustom(models.Model):
    _inherit = "product.template"

    limited_to_product_id = fields.Many2one('product.template', string="Limited to")