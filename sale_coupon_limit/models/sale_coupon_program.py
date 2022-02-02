# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, models


class SaleCouponProgram(models.Model):
    _inherit = "sale.coupon.program"

    def _check_promo_code(self, order, coupon_code):
        """Add customer and salesmen limit to program rules. Check the error strings
        for a detailed case detail."""
        message = super()._check_promo_code(order, coupon_code)
        if message:
            return message
        # The module sale_couopon_selection_wizard works with new records to probe
        # if a promotion is applicable before apply it for sure. Thus we need to ensure
        # the right id in the domain.
        domain = [("id", "!=", order._origin.id), ("state", "!=", "cancel")] + (
            [("promo_code", "=", coupon_code)]
            if coupon_code
            else [("no_code_promo_program_ids", "in", self.ids)]
        )
        # Customer limit rules
        if self.rule_max_customer_application:
            customer_domain = domain + [
                ("commercial_partner_id", "=", order.commercial_partner_id.id,),
            ]
            order_count = self.env["sale.order"].search_count(customer_domain)
            limit_reached = order_count >= self.rule_max_customer_application
            if limit_reached and coupon_code:
                return {
                    "error": _(
                        "This promo code was already applied %s times for this "
                        "customer and there's an stablished limit of %s for this "
                        "promotion."
                    )
                    % (order_count, self.rule_max_customer_application)
                }
            elif limit_reached and not coupon_code:
                return {
                    "error": _(
                        "This promotion was already applied %s times for this "
                        "customer and there's an stablished limit of %s."
                    )
                    % (order_count, self.rule_max_customer_application)
                }
        # Salesmen limit rules
        salesman_rule = self.rule_salesmen_limit_ids.filtered(
            lambda x: order.user_id == x.rule_user_id
        )
        max_rule = salesman_rule.rule_max_salesman_application
        times_used = salesman_rule.rule_times_used
        if times_used and times_used >= max_rule:
            return {
                "error": _(
                    "This promo code was already applied %s times for this "
                    "salesman and there's an stablished limit of %s for this "
                    "promotion."
                )
                % (times_used, max_rule)
            }
        if self.rule_salesmen_strict_limit and not salesman_rule:
            return {"error": _("This promotion is restricted to the listed salesmen.")}
        return message
