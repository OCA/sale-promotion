from odoo import fields, models


class PartnerReferral(models.Model):
    """A customer's participation in a referral program: one code per
    (partner, program), owning the promo rule that carries it."""

    _name = "loyalty.referral"
    _description = "Partner Referral Code"
    _rec_name = "code"
    _partner_program_uniq = models.Constraint(
        "UNIQUE(partner_id, program_id)",
        "A customer can have only one referral code per program.",
    )
    _code_uniq = models.Constraint("UNIQUE(code)", "Referral codes must be unique.")

    partner_id = fields.Many2one(
        "res.partner", required=True, ondelete="cascade", index=True
    )
    program_id = fields.Many2one("loyalty.program", required=True, ondelete="cascade")
    rule_id = fields.Many2one(
        "loyalty.rule",
        required=True,
        ondelete="cascade",
        help="The program's shared promotion rule this code activates.",
    )
    code = fields.Char(required=True, index=True)
    referral_url = fields.Char(compute="_compute_referral_url", compute_sudo=True)

    def _compute_referral_url(self):
        Partner = self.env["res.partner"]
        config = self.env["ir.config_parameter"].sudo().get_param
        default = Partner._get_referral_base_url()
        for rec in self:
            base = (
                f"{config('web.base.url')}{rec.program_id.referral_base_url}"
                if rec.program_id.referral_base_url
                else default
            )
            rec.referral_url = (
                f"{base}?referral={rec.code}" if base and rec.code else False
            )
