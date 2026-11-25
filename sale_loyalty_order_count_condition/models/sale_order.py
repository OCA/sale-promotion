from odoo import models


class SaleOrder(models.Model):
    _name = "sale.order"
    _inherit = "sale.order"

    def _program_check_compute_points(self, programs):
        # Gate programs whose order-count condition is not met, then programs
        # whose applicable rules all carry an unmet condition. A rule is
        # "applicable" when it is an automatic rule or its code was enabled on
        # this order.
        result = super()._program_check_compute_points(programs)
        for program, status in result.items():
            if "points" not in status:
                continue
            if (
                program.customer_order_condition
                and not program._customer_order_condition_met(self)
            ):
                del status["points"]
                status["error"] = program._customer_order_condition_message(self)
                continue
            applicable = program.rule_ids.filtered(
                lambda r: r.mode != "with_code" or r in self.code_enabled_rule_ids
            )
            conditioned = applicable.filtered("customer_order_condition")
            if (
                conditioned
                and conditioned == applicable
                and not any(
                    rule._customer_order_condition_met(self) for rule in conditioned
                )
            ):
                del status["points"]
                status["error"] = conditioned[0]._customer_order_condition_message(self)
        return result

    def action_confirm(self):
        before = {
            order.id: order.order_line.filtered("is_reward_line") for order in self
        }
        res = super().action_confirm()
        for order in self:
            removed = before.get(order.id) - order.order_line
            if removed:
                # Rewards can be dropped at confirm when conditions stop
                # holding (e.g. a first-order condition no longer matches) —
                # surface it instead of removing them silently.
                order.message_post(
                    body=self.env._(
                        "The reward %(rewards)s was removed: its conditions "
                        "are no longer met.",
                        rewards=", ".join(removed.mapped("name")),
                    ),
                    message_type="comment",
                )
        return res
