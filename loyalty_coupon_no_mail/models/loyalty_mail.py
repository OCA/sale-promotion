from odoo import fields, models


class LoyaltyMailInherit(models.Model):
    _inherit = "loyalty.mail"

    trigger = fields.Selection(
        selection_add=[("never", "Never")],
        default="never",
        ondelete={"never": "cascade"},
    )
