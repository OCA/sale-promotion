from odoo import fields, models


class LoyaltyRule(models.Model):
    _name = "loyalty.rule"
    _inherit = "loyalty.rule"

    is_referral_rule = fields.Boolean(
        help="Shared promotion rule activated by this program's referral "
        "codes. Referral codes live on loyalty.referral records, not on "
        "individual rules."
    )
