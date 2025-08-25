from odoo import Command, _, api, fields, models


class SaleLoyaltyRewardWizard(models.TransientModel):
    _inherit = "sale.loyalty.reward.wizard"
    _description = "Sale Loyalty - Reward Selection Wizard"

    product_id = fields.Many2one("product.product")
    # To ensure whether the selected promotion satisfies your rules and is directly
    # applicable or needs to satisfy your rules to be applied.
    applicable_program = fields.Boolean(
        compute="_compute_applicable_promotion",
        default="True",
    )
    loyalty_rule_line_ids = fields.One2many(
        comodel_name="sale.loyalty.rule.product_line.wizard",
        inverse_name="wizard_id",
        compute="_compute_loyalty_rule_line_ids",
        store=True,
        readonly=False,
        string="Loyalty Rule Lines",
    )
    loyalty_rule_line_description = fields.Html(
        compute="_compute_loyalty_rule_line_description"
    )

    @api.depends("reward_ids", "selected_reward_id")
    def _compute_applicable_promotion(self):
        self.order_id._update_programs_and_rewards()
        claimable_rewards = self.order_id._get_claimable_rewards()
        if self.selected_reward_id in claimable_rewards.values():
            self.applicable_program = True
        else:
            self.applicable_program = False

    @api.depends("selected_reward_id")
    def _compute_loyalty_rule_line_ids(self):
        self.loyalty_rule_line_ids = None
        units_required = min(
            self.selected_reward_id.program_id.rule_ids.mapped("minimum_qty"), default=0
        )
        if (
            self.selected_reward_id
            and not self.applicable_program
            and units_required > 0
        ):
            lines_vals = []
            products = [
                product
                for rule in self.selected_reward_id.program_id.rule_ids
                for product in rule._get_valid_products()
            ]
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
                            "units_required": units_required,
                            "units_included": units_included or 0,
                        },
                    )
                )
            self.loyalty_rule_line_ids = lines_vals

    @api.depends_context("lang")
    @api.depends("selected_reward_id")
    def _compute_loyalty_rule_line_description(self):
        self.loyalty_rule_line_description = False
        units_required = min(
            self.selected_reward_id.program_id.rule_ids.mapped("minimum_qty"), default=0
        )
        if (
            self.selected_reward_id
            and not self.applicable_program
            and units_required > 0
        ):
            products = self.loyalty_rule_line_ids.mapped("product_id.name")
            if len(products) > 1:
                products_str = f"{', '.join(products[:-1])} {_('or')} {products[-1]}"
            else:
                products_str = products[0] if products else ""
            self.loyalty_rule_line_description = _(
                "<b>* Required quantity:</b> %(units)s units of %(products)s"
            ) % {
                "units": units_required,
                "products": products_str,
            }

    def _update_order_line_with_units(self, order_line, units):
        """Updates an existing order line with the provided units."""
        order_line.write({"product_uom_qty": order_line.product_uom_qty + units})

    def _create_new_order_line(self, product, units):
        """Creates a new order line with the product and units provided."""
        self.order_id.order_line.create(
            {
                "order_id": self.order_id.id,
                "product_id": product.id,
                "product_uom_qty": units,
            }
        )

    def _apply_loyalty_rule_lines_to_order(self):
        for line in self.loyalty_rule_line_ids.filtered(
            lambda x: x.units_to_include > 0
        ):
            # Filter existing order lines based on the product of the loyalty rule line
            order_line = self.order_id.order_line.filtered(
                lambda x, line=line: x.product_id == line.product_id
            )
            if order_line:
                self._update_order_line_with_units(order_line, line.units_to_include)
            else:
                self._create_new_order_line(line.product_id, line.units_to_include)
        self.order_id._update_programs_and_rewards()

    def action_apply(self):
        # Added `skip_apply_loyalty_rule_lines` context check in to allow dependent
        # modules to control when _apply_loyalty_rule_lines_to_order is executed.
        if not self.env.context.get("skip_apply_loyalty_rule_lines"):
            self._apply_loyalty_rule_lines_to_order()
        super().action_apply()
        return {
            "type": "ir.actions.client",
            "tag": "soft_reload",
        }


class SaleLoyaltyRuleProductLineWizard(models.TransientModel):
    _name = "sale.loyalty.rule.product_line.wizard"
    _description = "Sale Loyalty Rule Product Line Wizard"

    wizard_id = fields.Many2one(comodel_name="sale.loyalty.reward.wizard")
    order_id = fields.Many2one(related="wizard_id.order_id", store=True)
    company_id = fields.Many2one(related="order_id.company_id")
    currency_id = fields.Many2one(related="order_id.currency_id")
    product_id = fields.Many2one(comodel_name="product.product")
    price_unit = fields.Float(string="Unit Price", compute="_compute_price_unit")
    pricelist_id = fields.Many2one(related="wizard_id.order_id.pricelist_id")
    units_included = fields.Float(string="Included units")
    units_required = fields.Float(string="Required units")
    units_to_include = fields.Float(string="Units to include")

    @api.depends("wizard_id")
    def _compute_price_unit(self):
        for record in self.filtered(lambda x: x.product_id):
            pricelist_rule_id = record.pricelist_id._get_product_rule(
                record.product_id,
                1.0,
                uom=record.product_id.uom_id,
                date=record.order_id.date_order,
            )
            pricelist_rule = record.env["product.pricelist.item"].browse(
                pricelist_rule_id
            )
            price_rule = pricelist_rule._compute_price(
                record.product_id,
                record.units_included,
                record.product_id.uom_id,
                record.order_id.date_order,
                currency=record.currency_id,
            )
            record.price_unit = record.product_id._get_tax_included_unit_price(
                record.order_id.company_id,
                record.currency_id,
                record.order_id.date_order,
                "sale",
                fiscal_position=record.order_id.fiscal_position_id,
                product_price_unit=price_rule,
                product_currency=record.currency_id,
            )
