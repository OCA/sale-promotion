# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from ast import literal_eval

from odoo import api, fields, models
from odoo.osv import expression


class LoyaltyProgram(models.Model):
    _inherit = "loyalty.program"

    mailing_ids = fields.One2many(
        comodel_name="mailing.mailing",
        inverse_name="program_id",
        string="Mailings",
        copy=False,
    )
    mailing_count = fields.Integer(
        compute="_compute_mailing_count", string="Mailing count"
    )

    partner_applicability_domain = fields.Char(
        compute="_compute_partner_applicability_domain",
    )

    @api.depends("rule_ids.rule_partners_domain")
    def _compute_partner_applicability_domain(self):
        for program in self:
            partner_domains = [
                literal_eval(domain)
                for domain in program.rule_ids.mapped("rule_partners_domain")
                if domain
            ]
            if all(partner_domains):
                program.partner_applicability_domain = expression.OR(partner_domains)
            else:
                program.partner_applicability_domain = "[]"

    @api.depends("mailing_ids")
    def _compute_mailing_count(self):
        mailing_data = self.env["mailing.mailing"].read_group(
            [("program_id", "in", self.ids)], ["program_id"], ["program_id"]
        )
        mapped_data = {m["program_id"][0]: m["program_id_count"] for m in mailing_data}
        for program in self:
            program.mailing_count = mapped_data.get(program.id, 0)

    def action_mailing_count(self):
        self.ensure_one()
        xmlid = "mass_mailing.mailing_mailing_action_mail"
        model = self.env["ir.model"].sudo().search([("model", "=", "res.partner")])
        if not self.mailing_count:
            mailing = self.env["mailing.mailing"].create(
                {
                    "program_id": self.id,
                    "mailing_model_id": model.id,
                    "subject": self.name,
                    "mailing_domain": self.partner_applicability_domain,
                }
            )
            result = self.env["ir.actions.act_window"]._for_xml_id(xmlid)
            result["res_id"] = mailing.id
            res = self.env.ref("mass_mailing.view_mail_mass_mailing_form", False)
            result["views"] = [(res and res.id or False, "form")]
        else:
            result = self.env["ir.actions.act_window"]._for_xml_id(xmlid)
            result["domain"] = [("id", "in", self.mailing_ids.ids)]
        # Set context and add defaults
        result["context"] = dict(self.env.context)
        result["context"]["default_mailing_model_id"] = model.id
        result["context"]["default_program_id"] = self.id
        result["context"]["default_subject"] = self.name
        if self.partner_applicability_domain:
            result["context"][
                "default_mailing_domain"
            ] = self.partner_applicability_domain
        return result
