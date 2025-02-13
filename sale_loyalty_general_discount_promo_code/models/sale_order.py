from odoo import _, models
from odoo.tools import format_amount


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_total_saving_specific(self, reward):
        self.ensure_one()
        assert reward.discount_applicability == "specific"

        order_lines = self.order_line - self._get_no_effect_on_threshold_lines()
        lines_to_discount = order_lines.filtered(
            lambda line: not line.reward_id
            and line.product_uom_qty
            and line.price_total
            and line.product_id.filtered_domain(reward._get_discount_product_domain())
        )

        return sum(
            line.price_unit * line.product_uom_qty * (reward.discount / 100)
            for line in lines_to_discount
        )

    def _get_total_saving_cheapest(self, reward):
        self.ensure_one()
        assert reward.discount_applicability == "cheapest"

        cheapest_line = self._cheapest_line()
        if not cheapest_line:
            return 0
        return (
            cheapest_line.price_unit
            * cheapest_line.product_uom_qty
            * (reward.discount / 100)
        )

    def _get_total_saving_order(self, reward):
        self.ensure_one()
        assert reward.discount_applicability == "order"
        total_saving = 0
        for line in self.order_line:
            if line.reward_id:
                continue
            total_saving += (
                line.price_unit * line.product_uom_qty * (reward.discount / 100)
            )
        return total_saving

    def _get_total_saved_amount(self, reward):
        total_saving = 0
        reward_applies_on = reward.discount_applicability
        if reward_applies_on == "order":
            total_saving = self._get_total_saving_order(reward)
        elif reward_applies_on == "specific":
            total_saving = self._get_total_saving_specific(reward)
        elif reward_applies_on == "cheapest":
            total_saving = self._get_total_saving_cheapest(reward)

        return format_amount(self.env, total_saving, self.pricelist_id.currency_id)

    def _get_reward_values_discount(self, reward, coupon, **kwargs):
        rewards = super()._get_reward_values_discount(reward, coupon, **kwargs)

        if (
            not self.env["ir.config_parameter"]
            .sudo()
            .get_param(
                "sale_loyalty_general_discount_promo_code."
                "automatically_apply_promo_code_discount_percentage"
            )
        ):
            return rewards

        # Display percentage discount as a single note line rather than multiple discount lines
        if (
            reward.reward_type == "discount"
            and reward.discount_mode == "percent"
            and (
                reward.program_id.program_type in ["coupons", "promo_code", "promotion"]
            )
        ):
            # Get the saved amount
            # Cannot use the reward_line.price_unit for the saved amount
            # because _get_reward_line_values is called twice.
            # Once in _apply_program_reward and once in _update_programs_and_rewards
            saved_amount = self._get_total_saved_amount(reward)

            if rewards:
                first_reward = rewards[0]
                first_reward.update(
                    {
                        "display_type": "line_note",
                        "name": _(
                            f"You saved {saved_amount} with promo '{reward.program_id.name}'"
                        ),
                        "price_unit": 0,
                        "product_uom_qty": 0,
                        "product_id": None,
                        "product_uom": None,
                    }
                )
                return [first_reward]

        return rewards

    def update_discount_percentage(self):
        self.ensure_one()
        reward_lines = self.order_line.filtered(lambda line: line.reward_id)
        order_lines = self.order_line - reward_lines

        reward_groups = {"cheapest": [], "specific": [], "order": []}
        for reward_line in reward_lines:
            reward = reward_line.reward_id
            if reward.discount_mode == "percent":
                reward_groups[reward.discount_applicability].append(reward)

        cheapest_line = self._cheapest_line() if reward_groups["cheapest"] else None
        specific_domains = {
            reward: reward._get_discount_product_domain()
            for reward in reward_groups["specific"]
        }

        for line in order_lines:

            # Update discount based on `order` rewards
            for reward in reward_groups["order"]:
                line.apply_reward(reward)

            # Update discount based on `cheapest` rewards
            if line == cheapest_line:
                for reward in reward_groups["cheapest"]:
                    line.apply_reward(reward)

            # Update discount based on `specific` rewards
            for reward, domain in specific_domains.items():
                if line.product_id.filtered_domain(domain):
                    line.apply_reward(reward)

    def _write_vals_from_reward_vals(self, reward_vals, old_lines, delete=True):
        result = super()._write_vals_from_reward_vals(
            reward_vals, old_lines, delete=delete
        )
        if (
            not self.env["ir.config_parameter"]
            .sudo()
            .get_param(
                "sale_loyalty_general_discount_promo_code."
                "automatically_apply_promo_code_discount_percentage"
            )
        ):
            return result
        self.update_discount_percentage()
        return result
