# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def write(self, vals):
        """We're looking for reward lines set in the write, from those, we'll get
        the proper ids to write them into the related lines"""
        res = super().write(vals)
        reward_lines = self.order_line.filtered(
            lambda x: x.loyalty_program_id and x.is_reward_line
        )
        if not reward_lines:
            return res
        programs = reward_lines.loyalty_program_id
        for order in self:
            order._link_reward_lines(programs)
            order._link_reward_generated_lines(programs)
        return res

    def _get_discounted_lines(self, program):
        """Hook method that allows to link lines from extra discount reward options"""
        # TODO: Should we add the lines that meet the criteria even if they aren't
        # on the filtered lines?
        lines = self.env["sale.order.line"]
        for reward in program.reward_ids:
            if reward.discount_applicability == "order":
                lines = self.order_line.filtered(lambda x: not x.is_reward_line)
            elif reward.discount_applicability == "cheapest":
                lines = self._cheapest_line()
            elif reward.discount_applicability == "specific":
                lines = self._get_specific_discountable_lines(reward)
        # An extra discount scope could not depend no this module. For integration
        # purposes, allways return at least an empty object
        return lines

    def _link_reward_discount_lines(self, program):
        """Assign reward lines depending on the discount scope of the promotion:
        - A discount on order, will apply to every line.
        - A discount on the cheapest product just to the cheapest line.
        - A discount on specific products only on those products defined in the
          promotion and available in the order lines.
        Thes filters are the same the core methods use.
        """
        reward_lines = self.order_line.filtered(
            lambda x: x.loyalty_program_id == program
        )
        lines = self._get_discounted_lines(program)
        # Distribute different tax reward lines with their correspondant order lines.
        # We use a dictionary so we can compare taxes even if they are composed.
        tax_reward_map = {}
        for reward_line in reward_lines:
            tax_reward_map.setdefault(reward_line.tax_id, self.env["sale.order.line"])
            tax_reward_map[reward_line.tax_id] |= reward_line
        for tax, tax_reward_lines in tax_reward_map.items():
            lines.filtered(lambda x: x.tax_id == tax).write(
                {"reward_line_ids": [(4, rl.id) for rl in tax_reward_lines]}
            )

    def _link_reward_product_lines(self, program):
        """We want to link to the reward those lines that generated it as well as
        the rewarded product, that could be not in the original domain"""
        reward_lines = self.order_line.filtered(
            lambda x: x.loyalty_program_id == program
        )
        lines_with_reward_product_id = self.order_line.filtered(
            lambda x: any(
                r.reward_product_id == x.product_id for r in program.reward_ids
            )
        )
        # We'll just consider as many lines as the reward quantity can cover.
        lines = self.env["sale.order.line"]
        for reward in program.reward_ids:
            reward_qty = reward.reward_product_qty
            for line in lines_with_reward_product_id:
                lines |= line
                if line.product_uom_qty >= reward_qty:
                    break
                reward_qty -= line.product_uom_qty
        lines.write({"reward_line_ids": [(4, rl.id) for rl in reward_lines]})

    def _link_reward_lines(self, programs):
        """We want to filter the lines that generated a condition and link them to
        the generated rewards. Every reward type has it's own cases depending on
        how's applied. Another reward types (e.g: sale_loyalty_delivery) should extend
        this method adding its cases. Also to be noted that a single line could
        generate several rewards coming from different promotions."""
        for program in programs:
            rewards = program.reward_ids
            for _reward in rewards.filtered(lambda x: x.reward_type == "discount"):
                self._link_reward_discount_lines(program)
            for _reward in rewards.filtered(lambda x: x.reward_type == "product"):
                self._link_reward_product_lines(program)

    def _link_reward_generated_lines(self, programs):
        """Link the lines that generated reward lines to those lines"""
        for program in programs:
            reward_lines = self.order_line.filtered(
                lambda x: x.loyalty_program_id == program
            )
            self.order_line._filter_related_program_lines(program).write(
                {"reward_generated_line_ids": [(4, rl.id) for rl in reward_lines]}
            )


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    loyalty_program_id = fields.Many2one(
        related="reward_id.program_id", store=True, string="Loyalty Program"
    )
    reward_line_ids = fields.Many2many(
        comodel_name="sale.order.line",
        relation="sale_line_reward_line_rel",
        column1="sale_line_id",
        column2="reward_line_id",
        string="Reward lines",
        help="Link on the reward lines applied from this one",
    )
    reward_generated_line_ids = fields.Many2many(
        comodel_name="sale.order.line",
        relation="sale_line_reward_generated_line_rel",
        column1="sale_line_id",
        column2="reward_generated_line_id",
        string="Reward Generated lines",
        help="Link on the reward lines generated meeting this line as criteria",
    )
    reward_origin_generated_line_ids = fields.Many2many(
        comodel_name="sale.order.line",
        relation="sale_line_reward_generated_line_rel",
        column1="reward_generated_line_id",
        column2="sale_line_id",
        string="Origin Reward Generated lines",
        help="Origin Link on the reward lines generated meeting this line as criteria",
    )

    def write(self, vals):
        """When the reward line is update we should refresh the line links as well"""
        res = super().write(vals)
        if self.filtered(lambda x: x.is_reward_line and x.loyalty_program_id):
            program = self.env["loyalty.program"].browse([self.loyalty_program_id.id])
            for order in self.mapped("order_id"):
                order._link_reward_lines(program)
        return res

    def _filter_related_program_lines(self, program):
        """Discard those lines not in the program domain. With other modules changing
        the product criteria rules, we can extend this method to return the proper
        records."""
        rule_domains = [rule._get_valid_product_domain() for rule in program.rule_ids]
        if not rule_domains:
            return self.filtered(lambda x: not x.is_reward_line)
        valid_product_ids = set()
        for domain in rule_domains:
            valid_products = self.mapped("product_id").filtered_domain(domain)
            valid_product_ids.update(valid_products.ids)
        return self.filtered(
            lambda x: x.product_id.id in valid_product_ids and not x.is_reward_line
        )
