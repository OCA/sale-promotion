# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, models


class SaleCoupon(models.Model):
    _inherit = "sale.coupon"

    def _check_coupon_code(self, order):
        """Add customer and salesmen limit to program coupons. Check the error strings
        for a detailed case detail."""
        message = super()._check_coupon_code(order)
        if message:
            return message
        domain = [
            ("order_id", "!=", order.id),
            ("program_id", "=", self.program_id.id),
            ("state", "=", "used"),
        ]
        # Customer limit rules
        if self.program_id.rule_max_customer_application:
            coupons_count = self.search_count(
                domain
                + [
                    (
                        "sales_order_id.commercial_partner_id",
                        "=",
                        order.commercial_partner_id.id,
                    )
                ]
            )
            if coupons_count >= self.program_id.rule_max_customer_application:
                return {
                    "error": _(
                        "This promotion was already applied %s times for this "
                        "customer and there's an stablished limit of %s."
                    )
                    % (coupons_count, self.program_id.rule_max_customer_application)
                }
        # Salesmen limit rules
        salesman_rule = self.program_id.rule_salesmen_limit_ids.filtered(
            lambda x: order.user_id == x.rule_user_id
        )
        max_rule = salesman_rule.rule_max_salesman_application
        times_used = salesman_rule.rule_times_used
        if times_used and times_used >= max_rule:
            return {
                "error": _(
                    "This promotion was already applied %s times for this "
                    "salesman and there's an stablished limit of %s."
                )
                % (times_used, max_rule)
            }
        if self.program_id.rule_salesmen_strict_limit and not salesman_rule:
            return {"error": _("This promotion is restricted to the listed salesmen.")}
        return message
