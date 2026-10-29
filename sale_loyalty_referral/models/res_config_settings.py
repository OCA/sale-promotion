from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    referral_program_id = fields.Many2one(
        "loyalty.program",
        string="Referral Program",
        config_parameter="sale_loyalty_referral.referral_program_id",
        domain=[("program_type", "=", "promo_code")],
        help="Discount Code program whose rules mint each customer's personal "
        "referral code.",
    )
    referral_portal_card = fields.Boolean(
        string="Portal referral card",
        default=True,
        config_parameter="sale_loyalty_referral.referral_portal_card",
        help="Show the referral card at the bottom of the portal home page.",
    )
    referral_base_url = fields.Char(
        string="Referral Base URL",
        config_parameter="sale_loyalty_referral.referral_base_url",
        help="Landing page used in personal referral links. The customer's code "
        "is appended as a ?referral= parameter; any Odoo page works, e.g. / "
        "or /appointment. Defaults to /.",
    )
