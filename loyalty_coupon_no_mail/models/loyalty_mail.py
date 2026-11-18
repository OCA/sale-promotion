from odoo import fields, models


class LoyaltyMailInherit(models.Model):
    _inherit = "loyalty.mail"

    trigger = fields.Selection(
        selection_add=[("never", "Never")],
        default="never",
        ondelete={"never": "cascade"},
    )
    mail_template_id = fields.Many2one(
        default=lambda self: (
            self.env.ref("loyalty.mail_template_loyalty_card", raise_if_not_found=False)
            or self.env["mail.template"]
        ).id,
    )
