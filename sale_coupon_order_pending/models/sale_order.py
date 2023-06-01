# Copyright 2023 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.osv import expression


class SaleOrder(models.Model):
    _inherit = "sale.order"

    pending_partner_coupon_count = fields.Integer(
        compute="_compute_pending_partner_coupon_count",
        compute_sudo=True,
    )

    def _partner_coupon_domain(self):
        """For compatibility with sale_coupon_apply_commercial_partner"""
        return [("partner_id", "=", self.partner_id.id)]

    def _pending_coupon_domain(self):
        """Override to do a broader search"""
        return expression.AND(
            [
                [("state", "in", ("new", "sent")), ("order_id", "!=", self.id)],
                self._partner_coupon_domain(),
            ]
        )

    @api.depends("partner_id")
    def _compute_pending_partner_coupon_count(self):
        """Give a hint to the salesman about pending coupons for this parnter"""
        self.pending_partner_coupon_count = 0
        for sale in self.filtered("partner_id"):
            sale.pending_partner_coupon_count = self.env["coupon.coupon"].search_count(
                sale._pending_coupon_domain()
            )

    def action_view_pending_partner_coupons(self):
        """View partner pending coupons"""
        self.ensure_one()
        coupon_obj = self.env["coupon.coupon"]
        # Done for compatibility sake with sales_team_security
        if self.user_has_groups("sales_team.group_sale_salesman"):
            coupon_obj = coupon_obj.sudo()
        pending_partner_coupon_ids = coupon_obj._search(self._pending_coupon_domain())
        return {
            "type": "ir.actions.act_window",
            "name": _("Coupons pending for %(customer)s")
            % {"customer": self.partner_id.name},
            "view_mode": "kanban,form",
            "res_model": "coupon.coupon",
            "target": "current",
            "context": {"active_id": self.id, "active_model": "sale.order"},
            "domain": [("id", "in", list(pending_partner_coupon_ids))],
        }
