from odoo import _, api, fields, models
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
        # The products of the rule with criteria "multi_product" related to the product_id
        # of the line are taken into consideration in case the line contains a product of
        # the rules, otherwise the product_id will coincide with a reward product and in
        # that case the products of the first rule "multi_product" are taken into consideration.
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
                    lambda x: x.product_id == record and not x.is_reward_line
                ).product_uom_qty
                lines_vals.append(
                    (
                        0,
                        0,
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
        products = list(
            set(
                self.selected_reward_id.program_id.rule_ids.loyalty_criteria_ids.product_ids
            )
        )
        if self.selected_reward_id and not self.applicable_program and products:
            if len(products) > 1:
                products_str = f"{', '.join(map(str, [product.name for product in products][:-1]))} {_('and')} {[product.name for product in products][-1]}"  # noqa: B950
            self.loyalty_rule_line_description = (
                f"<b>* {_('Required quantity')}:</b> 1 {_('unit of')} {products_str}"
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
                return super().action_apply()
            else:
                raise ValidationError(
                    _("The quantities necessary to apply the promotion are not added.")
                )
        else:
            return super().action_apply()


class SaleLoyaltyRuleProductLineWizard(models.TransientModel):
    _inherit = "sale.loyalty.rule.product_line.wizard"

    multi_criteria = fields.Boolean(related="wizard_id.multi_criteria")
