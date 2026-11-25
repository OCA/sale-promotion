from odoo import api, fields, models
from odoo.exceptions import ValidationError


class LoyaltyProgram(models.Model):
    _name = "loyalty.program"
    _inherit = "loyalty.program"

    is_referral = fields.Boolean(
        string="Referral Program",
        help="This program issues partner referral codes. The program "
        "selected in Sales > Settings > Customer Referrals is the default "
        "used by the portal and partner actions; additional programs can be "
        "flagged to mint codes for their own campaign.",
    )
    is_default_referral = fields.Boolean(
        compute="_compute_is_default_referral",
        help="This program is selected as the referral program in Sales settings.",
    )
    referral_code_count = fields.Integer(compute="_compute_referral_code_count")
    referral_base_url = fields.Char(
        help="Landing page used in this program's referral links; the "
        "partner's code is appended as a ?referral= parameter. Falls back to "
        "the setting in Sales > Settings > Customer Referrals, then /."
    )
    referral_message = fields.Char(
        help="Optional guidance shown to visitors whose referral code could "
        "not yet be applied (e.g. 'Add 2 items to unlock your friend's "
        "discount').",
    )
    referral_retention_days = fields.Integer(
        string="Attribution Window (days)",
        default=31,
        help="Days a link click keeps attributing orders to the referrer. "
        "Set to 0 to keep attribution for the browser session only.",
    )

    @api.constrains("is_referral", "program_type")
    def _check_is_referral(self):
        if any(p.is_referral and p.program_type != "promo_code" for p in self):
            raise ValidationError(
                self.env._("Only Discount Code programs can be referral programs.")
            )

    def _compute_is_default_referral(self):
        program = self.env["res.partner"]._get_referral_program()
        for rec in self:
            rec.is_default_referral = rec in program

    def _compute_referral_code_count(self):
        counts = {
            program.id: count
            for program, count in self.env["loyalty.referral"]._read_group(
                [("program_id", "in", self.ids)],
                ["program_id"],
                ["__count"],
            )
        }
        for rec in self:
            rec.referral_code_count = counts.get(rec.id, 0)

    def action_open_referral_codes(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Referral Codes"),
            "res_model": "loyalty.referral",
            "view_mode": "list,form",
            "domain": [("program_id", "=", self.id)],
        }

    def action_generate_referral_codes(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Generate Referral Code"),
            "res_model": "loyalty.referral.generate.wizard",
            "view_mode": "form",
            "target": "new",
        }

    @api.model
    def get_program_templates(self):
        templates = super().get_program_templates()
        if self.env.context.get("menu_type") != "gift_ewallet":
            templates["referral"] = {
                "title": self.env._("Referral"),
                "description": self.env._(
                    "Customers share a personal link; friends redeem the "
                    "embedded code on their first order"
                ),
                "icon": "promotional_program",
            }
        return templates

    @api.model
    def _get_template_values(self):
        # Referral programs are plain promo_code programs: rules are minted
        # per customer on code generation, only the reward is preset.
        values = super()._get_template_values()
        values["referral"] = {
            "name": self.env._("Referral"),
            "program_type": "promo_code",
            "applies_on": "current",
            "trigger": "with_code",
            "is_referral": True,
            "rule_ids": [(5, 0, 0)],
            "reward_ids": [
                (
                    0,
                    0,
                    {
                        "reward_type": "discount",
                        "discount": 10,
                        "discount_mode": "per_order",
                        "discount_applicability": "order",
                    },
                )
            ],
        }
        return values

    @api.model
    def create_from_template(self, template_id):
        action = super().create_from_template(template_id)
        # _compute_from_program_type injects promo_code's default random-code
        # rule on create; referral rules are minted per customer instead.
        if template_id == "referral" and action:
            self.browse(action["res_id"]).rule_ids.unlink()
        return action
