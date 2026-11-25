from odoo import fields, models


class PartnerReferralGenerateWizard(models.TransientModel):
    _name = "loyalty.referral.generate.wizard"
    _description = "Generate Referral Codes"

    partner_ids = fields.Many2many("res.partner", string="Customers", required=True)

    def action_generate(self):
        # Opened from a program form: mint codes for that program. The portal
        # and partner actions use the configured referral program instead.
        program = self.env["loyalty.program"]
        if self.env.context.get("active_model") == "loyalty.program":
            program = (
                self.env["loyalty.program"]
                .browse(self.env.context.get("active_id"))
                .exists()
            )
        for partner in self.partner_ids:
            partner.ensure_referral_code(program)
        if program:
            return program.action_open_referral_codes()
        return {"type": "ir.actions.act_window_close"}
