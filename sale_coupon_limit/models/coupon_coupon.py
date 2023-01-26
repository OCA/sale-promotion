# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, models


class SaleCoupon(models.Model):
    _inherit = "coupon.coupon"

    def _check_coupon_code(self, order_date, partner_id, **kwargs):
        """Add customer and salesmen limit to program coupons. Check the error strings
        for a detailed case detail."""
        message = super()._check_coupon_code(order_date, partner_id, **kwargs)
        order = kwargs.get("order")
        if message or not order:
            return message
        # The module sale_coupon_selection_wizard works with new records to probe
        # if a promotion is applicable before apply it for sure. Thus we need to ensure
        # the right id in the domain.
        domain = [
            ("order_id", "!=", order._origin.id),
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
                        "This promotion was already applied %(count)s times for this "
                        "customer and there's an stablished limit of %(max)s."
                    )
                    % {
                        "count": coupons_count,
                        "max": self.program_id.rule_max_customer_application,
                    }
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
                    "This promotion was already applied %(times)s times for this "
                    "salesman and there's an stablished limit of %(max)s."
                )
                % {"times": times_used, "max": max_rule}
            }
        if self.program_id.rule_salesmen_strict_limit and not salesman_rule:
            return {"error": _("This promotion is restricted to the listed salesmen.")}
        return message
