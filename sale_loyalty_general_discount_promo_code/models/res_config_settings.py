from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    automatically_apply_promo_code_discount_percentage = fields.Boolean(
        config_parameter=(
            "sale_loyalty_general_discount_promo_code."
            "automatically_apply_promo_code_discount_percentage"
        ),
    )
