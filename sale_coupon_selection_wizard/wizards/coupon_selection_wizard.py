# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class CouponSelectionWizard(models.TransientModel):
    _name = "coupon.selection.wizard"
    _description = "Select promotion to apply to the order"

    order_id = fields.Many2one(comodel_name="sale.order")
    pricelist_id = fields.Many2one(related="order_id.pricelist_id")
    available_coupon_program_ids = fields.Many2many(
        comodel_name="sale.coupon.program",
        compute="_compute_available_coupon_program_ids",
        searchable=False,
    )
    coupon_program_id = fields.Many2one(
        comodel_name="sale.coupon.program", default=False,
    )
    coupon_reward_name = fields.Char(
        related="coupon_program_id.reward_id.display_name",
    )
    promotion_line_ids = fields.One2many(
        comodel_name="coupon.selection.wizard.line", inverse_name="wizard_id",
    )

    def _existing_order_line(self, product_id):
        return self.order_id.sudo().order_line.filtered(
            lambda x: x.product_id == product_id and not x.is_reward_line
        )

    def _satisfied_product_quantities(self, product_id):
        return sum(self._existing_order_line(product_id).mapped("product_uom_qty"))

    def _prepare_promotion_line_vals(self, criteria, product_id):
        """Overridible in case we'd want to send something more to the controller"""
        current_order_quantity = self._satisfied_product_quantities(product_id)
        criteria_single_product = len(criteria.product_ids) == 1
        optional = criteria.repeat_product and not criteria_single_product
        criteria_qty = criteria.repeat_product and criteria.rule_min_quantity or 1
        qty_to_add = not optional and max(criteria_qty - current_order_quantity, 0) or 0
        return {
            "product_id": product_id.id,
            "current_order_quantity": current_order_quantity,
            "criteria_qty": criteria_qty,
            "criteria_id": criteria.id,
            "program_id": criteria.program_id.id,
            "optional": optional,
            "qty_to_add": qty_to_add,
        }

    @api.depends("order_id")
    def _compute_available_coupon_program_ids(self):
        """Load the data in the wizard. It will be managed by the controller"""
        for wizard in self:
            wizard.available_coupon_program_ids = False
            wizard.promotion_line_ids.unlink()
            available_coupon_program_ids = (
                wizard.order_id.sudo()._available_multi_criteria_multi_gift_programs()
            )
            # Compute all the programs possible criterias to use them in the widget
            promotion_line_ids = self.promotion_line_ids
            for criteria in available_coupon_program_ids.sale_coupon_criteria_ids:
                for product in criteria.product_ids:
                    promotion_line_ids += promotion_line_ids.new(
                        self._prepare_promotion_line_vals(criteria, product)
                    )
            wizard.available_coupon_program_ids = available_coupon_program_ids
            wizard.promotion_line_ids = promotion_line_ids


class CouponSelectionWizardProduct(models.TransientModel):
    _name = "coupon.selection.wizard.line"
    _description = "Products to apply to the promotion"

    wizard_id = fields.Many2one(comodel_name="coupon.selection.wizard")
    criteria_id = fields.Many2one(comodel_name="sale.coupon.criteria", readonly=True)
    program_id = fields.Many2one(comodel_name="sale.coupon.program", readonly=True)
    product_id = fields.Many2one(comodel_name="product.product", readonly=True)
    current_order_quantity = fields.Integer(
        readonly=True,
        help="Stores the quantity currently available in the order for this product",
    )
    rule_min_quantity = fields.Integer(related="criteria_id.rule_min_quantity")
    repeat_product = fields.Boolean(related="criteria_id.repeat_product")
    criteria_qty = fields.Integer(readonly=True)
    qty_to_add = fields.Integer(readonly=True)
    optional = fields.Boolean(readonly=True)

    def _get_program_options(self, program_id):
        program_lines = self.filtered(lambda x: x.program_id == program_id)
        program_lines_optional = program_lines.filtered(lambda x: not x.repeat_product)
        # Optional but single product
        program_lines_optional |= program_lines.filtered(
            lambda x: x.repeat_product and len(x.criteria_id.product_ids) == 1
        )
        # Tuple with mandatory options and optional options.
        return program_lines_optional, program_lines - program_lines_optional
