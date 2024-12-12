from odoo import _, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _program_check_compute_points(self, programs):
        res = super()._program_check_compute_points(programs)
        # Iterate through the programs that initially have no errors
        for program, result in res.items():
            if result.get("error", False):
                continue
            # Customer limit rules
            if program.max_customer_application:
                customer_domain = [
                    ("order_line.loyalty_program_id", "=", program.id),
                    ("id", "!=", self._origin.id),
                    (
                        "commercial_partner_id",
                        "=",
                        self.commercial_partner_id.id,
                    ),
                ]
                order_count = self.env["sale.order"].search_count(customer_domain)
                limit_reached = order_count >= program.max_customer_application
                if limit_reached and self.applied_coupon_ids:
                    res[program] = {
                        "error": _(
                            "This promo code was already applied %(count)s times for this "
                            "customer and there's an stablished limit of %(max)s for this "
                            "promotion."
                        )
                        % {
                            "count": order_count,
                            "max": program.max_customer_application,
                        }
                    }
                if limit_reached and not self.applied_coupon_ids:
                    res[program] = {
                        "error": _(
                            "This promotion was already applied %(count)s times "
                            "for this customer and there's an established limit "
                            "of %(max)s."
                        )
                        % {
                            "count": order_count,
                            "max": program.max_customer_application,
                        }
                    }
            # Salesmen limit rules
            salesman_rule = program.salesmen_limit_ids.filtered(
                lambda x: x.user_id.id == self.user_id.id
            )
            if salesman_rule:
                max_rule = salesman_rule.max_salesman_application
                # It is necessary to recalculate the number of times it has been used
                # omitting the current sell order because when a sell order is confirmed,
                # the "_update_programs_and_rewards" method is re-executed which triggers
                # the compute method again and in this method the current sell order is
                # not excluded.
                times_used = len(
                    self.env["sale.order.line"].read_group(
                        [
                            ("loyalty_program_id", "=", program.id),
                            (
                                "order_id.user_id",
                                "=",
                                salesman_rule.user_id.id,
                            ),
                            ("order_id.state", "!=", "cancel"),
                            ("order_id", "!=", self._origin.id),
                        ],
                        ["order_id"],
                        ["order_id"],
                    )
                )
                if times_used == 0 or times_used < max_rule:
                    continue
                if times_used >= max_rule:
                    res[program] = {
                        "error": _(
                            "This promo code was already applied %(times)s times for this "
                            "salesman and there's an stablished limit of %(max)s for this "
                            "promotion."
                        )
                        % {"times": times_used, "max": max_rule}
                    }
            if program.salesmen_strict_limit and not salesman_rule:
                res[program] = {
                    "error": _("This promotion is restricted to the listed salesmen.")
                }
        return res
