from odoo import Command, api, fields, models
from odoo.exceptions import ValidationError


class SaleLoyaltyRewardWizard(models.TransientModel):
    _inherit = "sale.loyalty.reward.wizard"

    multi_criteria = fields.Boolean(compute="_compute_multi_criteria")

    @api.depends("reward_ids", "selected_reward_id")
    def _compute_multi_criteria(self):
        self.multi_criteria = (
            self.selected_reward_id.program_id.rule_ids.loyalty_criteria
            == "multi_product"
        )

    def _compute_loyalty_rule_line_ids(self):
        self.loyalty_rule_line_ids = None
        # The products of the rule with criteria "multi_product" related to the
        # product_id of the line are taken into consideration in case the line contains
        # a product of the rules, otherwise the product_id will coincide with a reward
        # product and in that case the products of the first rule "multi_product" are
        # taken into consideration.
        products = (
            self.selected_reward_id.program_id.rule_ids.filtered(
                lambda x: x.loyalty_criteria == "multi_product"
                and self.product_id in x.loyalty_criteria_ids.product_ids
            )[:1].loyalty_criteria_ids.product_ids
            or self.selected_reward_id.program_id.rule_ids.filtered(
                lambda x: x.loyalty_criteria == "multi_product"
            )[:1].loyalty_criteria_ids.product_ids
        )
        if self.selected_reward_id and not self.applicable_program and products:
            lines_vals = []
            for record in products:
                units_included = self.order_id.order_line.filtered(
                    lambda x, record=record: x.product_id == record
                    and not x.is_reward_line
                ).product_uom_qty
                lines_vals.append(
                    Command.create(
                        {
                            "wizard_id": self.id,
                            "product_id": record.id,
                            "units_required": 1,
                            "units_included": units_included or 0,
                        },
                    )
                )
            self.loyalty_rule_line_ids = lines_vals
        else:
            return super()._compute_loyalty_rule_line_ids()

    def _compute_loyalty_rule_line_description(self):
        self.loyalty_rule_line_description = False
        products = (
            self.selected_reward_id.program_id.rule_ids.loyalty_criteria_ids.product_ids
        )
        if self.selected_reward_id and not self.applicable_program and products:
            if len(products) > 1:
                product_names = products.with_context(
                    display_default_code=False
                ).mapped("display_name")
                products_str = "{products_list} {and_word} {last_product}".format(
                    products_list=", ".join(product_names[:-1]),
                    and_word=self.env._("and"),
                    last_product=product_names[-1],
                )
            self.loyalty_rule_line_description = self.env._(
                "<b>* Required quantity:</b> 1 unit of %(products)s",
                products=products_str,
            )
        else:
            return super()._compute_loyalty_rule_line_description()

    def action_apply(self):
        if self.selected_reward_id.program_id.rule_ids.filtered(
            lambda x: x.loyalty_criteria == "multi_product"
        ):
            if all(
                line.units_to_include > 0 or line.units_included > 0
                for line in self.loyalty_rule_line_ids
            ):
                self._apply_loyalty_rule_lines_to_order()
                return super(
                    SaleLoyaltyRewardWizard,
                    self.with_context(skip_apply_loyalty_rule_lines=True),
                ).action_apply()
            else:
                raise ValidationError(
                    self.env._(
                        "The quantities necessary to apply the promotion are not added."
                    )
                )
        return super().action_apply()


class SaleLoyaltyRuleProductLineWizard(models.TransientModel):
    _inherit = "sale.loyalty.rule.product_line.wizard"

    multi_criteria = fields.Boolean(related="wizard_id.multi_criteria")
