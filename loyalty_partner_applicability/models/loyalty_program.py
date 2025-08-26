# Copyright 2023 Tecnativa - Pilar Vargas
# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.osv import expression
from odoo.tools.safe_eval import datetime, safe_eval


class LoyaltyProgram(models.Model):
    _inherit = "loyalty.program"

    partner_ids = fields.Many2many(
        string="Allowed partners",
        comodel_name="res.partner",
        help="Only the selected partners will be eligible for this promotion.",
        default=lambda p: p.env.context.get("default_partner_ids"),
    )

    partner_domain = fields.Char(
        string="Allowed partners domain",
        help="Define the domain to restrict which partners are eligible for this promotion.",
        default="[]",
    )

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for vals in vals_list:
            if not vals.get("partner_domain", False):
                vals["partner_domain"] = "[]"
        return res

    def _get_eval_partner_domain(self):
        self.ensure_one()
        return safe_eval(
            self.partner_domain,
            {"datetime": datetime, "context_today": datetime.datetime.now},
        )

    def _is_coupon_sharing_allowed(self):
        allow_sharing = (
            self.env["ir.config_parameter"].sudo().get_param("allow_coupon_sharing")
        )
        return allow_sharing and (
            allow_sharing.lower() == "true" or allow_sharing == "1"
        )

    def _get_partner_domain(self, partner):
        self.ensure_one()
        domain = []
        if (self.partner_domain and self.partner_domain != "[]") or self.partner_ids:
            if self._is_coupon_sharing_allowed():
                domain = [
                    ("commercial_partner_id", "=", partner.commercial_partner_id.id)
                ]

            else:
                domain = [("id", "=", partner.id)]

            partner_domain = []
            if self.partner_ids:
                partner_domain = [("id", "in", self.partner_ids.ids)]
            if self.partner_domain and self.partner_domain != "[]":
                partner_domain = expression.OR(
                    [partner_domain, self._get_eval_partner_domain()]
                )

            domain = expression.AND([domain, partner_domain])
        return domain

    def _is_partner_valid(self, partner):
        """
        Check if the partner is valid for the loyalty element

        If no restriction is set on partner, the partner is always valid
        If restrictions are set, the partner must match one of them.
        The matching varies depending on the coupon sharing setting:
        - If coupon sharing is not allowed, the partner must match one
        - If coupon sharing is allowed, the partner must match one or have
            the same commercial parent as a partner matching one restriction
        :param partner: res.partner record
        :return: bool
        """
        self.ensure_one()
        # If no restriction is set, the partner is always valid
        if not self.partner_ids and not self.partner_domain:
            return True
        coupon_sharing_allowed = self._is_coupon_sharing_allowed()
        # In any case, if restrictions are set and the partner matches them, it is valid
        partner_valid = True
        if self.partner_ids:
            partner_valid = partner in self.partner_ids
        if self.partner_domain and self.partner_domain != "[]":
            # (partner_valid and self.partner_ids) is required since we assume that if the
            # partner_ids is not set but the partner_domain is set, the partner must match the
            # partner_domain (IOW before we check the domain we assume that the partner is not
            # valid if partner_ids is not set and partner_domain is set)
            partner_valid = (partner_valid and bool(self.partner_ids)) or (
                partner.filtered_domain(self._get_eval_partner_domain()) == partner
            )
        # if the partner is not valid but coupon sharing is allowed, check if the partner has
        # the same commercial parent as the partner in the restrictions
        if not partner_valid and coupon_sharing_allowed:
            partner_domain = self._get_partner_domain(partner)
            partner_valid = self.env["res.partner"].search_count(partner_domain) > 0
        return partner_valid
