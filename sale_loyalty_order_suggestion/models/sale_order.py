# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models
from odoo.osv import expression


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_available_programs_domain(self):
        domain = [
            ("active", "=", True),
            ("trigger", "=", "auto"),
            ("program_type", "not in", ("promo_code", "next_order_coupons")),
            "|",
            ("date_from", "=", False),
            ("date_from", "<=", fields.Date.today()),
            "|",
            ("date_to", "=", False),
            ("date_to", ">=", fields.Date.today()),
            "|",
            ("applies_on", "=", "current"),
            ("applies_on", "=", "both"),
        ]
        return domain

    def _get_available_programs(self):
        programs = self.env["loyalty.program"]
        programs_applied = self._get_reward_programs()
        domain = expression.AND(
            [
                self._get_available_programs_domain(),
                [("id", "not in", programs_applied.ids)],
            ]
        )
        programs = (
            self.env["loyalty.program"]
            .search(domain)
            .filtered(lambda p: not p.limit_usage or p.total_order_count < p.max_usage)
        )
        # If the same reward has already been applied from another program, the reward
        # and the program to which it belongs must be deleted from the list of
        # suggestions. For example, if a 10% discount has already been applied, the same
        # discount cannot be applied even if it belongs to another program.
        order_rewards = self.order_line.reward_id
        programs_to_delete = []
        if order_rewards:
            programs_to_delete = [
                program.id
                for program in programs
                if any(
                    all(
                        getattr(program_reward, field) == getattr(order_reward, field)
                        for field in [
                            "reward_type",
                            "discount",
                            "discount_mode",
                            "discount_applicability",
                            "discount_product_domain",
                            "discount_product_ids",
                            "discount_product_category_id",
                            "discount_max_amount",
                            "reward_product_id",
                            "reward_product_tag_id",
                            "reward_product_qty",
                            "required_points",
                        ]
                    )
                    for program_reward in program.reward_ids
                    for order_reward in order_rewards
                )
            ]
        return programs.filtered(lambda p: p.id not in programs_to_delete)

    def _filter_programs_by_rules_with_products(self):
        """Hook method. The objective of this method is to filter by rules that
        establish products as criteria in a loyalty program and then in other methods
        make the filtering that corresponds to each functionality."""
        valid_programs = self._get_available_programs()
        # Filters programs that have rules with minimum_qty > 0
        programs_with_minimum_qty = valid_programs.filtered(
            lambda x: any(rule.minimum_qty > 0 for rule in x.rule_ids)
        )
        return programs_with_minimum_qty

    def _available_programs(self):
        self.ensure_one()
        filtered_programs = self._filter_programs_by_rules_with_products()
        programs = self.env["loyalty.program"]
        if filtered_programs:
            product_id = self.env.context.get("product_id")
            programs += filtered_programs.filtered(
                lambda x: any(
                    product_id in rule._get_valid_products().ids
                    and rule.minimum_qty > 0
                    for rule in x.rule_ids
                )
            )
        return programs


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    suggested_promotion_ids = fields.Many2many(
        comodel_name="loyalty.program",
        compute="_compute_suggested_promotion_ids",
    )
    suggested_promotions = fields.Boolean(
        compute="_compute_suggested_promotion_ids", default=False
    )
    suggested_reward_ids = fields.Many2many(
        comodel_name="loyalty.reward",
        compute="_compute_suggested_promotion_ids",
    )

    @api.depends("product_id")
    def _compute_suggested_promotion_ids(self):
        self.suggested_promotion_ids = False
        self.suggested_reward_ids = False
        self.suggested_promotions = False
        for line in self.filtered(
            lambda x: x.product_id and x.order_id.state != "done"
        ):
            line.suggested_promotion_ids = line.order_id.with_context(
                product_id=line.product_id.id
            )._available_programs()
            line.suggested_promotions = bool(line.suggested_promotion_ids)
            line.suggested_reward_ids = line.suggested_promotion_ids.reward_ids
