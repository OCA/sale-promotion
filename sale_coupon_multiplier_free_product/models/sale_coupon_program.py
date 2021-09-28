# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from operator import itemgetter

from odoo import _, api, models
from odoo.tools import pycompat


class SaleCouponProgram(models.Model):
    _inherit = "sale.coupon.program"

    @api.onchange("reward_type")
    def _onchange_reward_type_multiple_of(self):
        """We don't want this flag active in other options"""
        if self.reward_type != "multiple_of":
            self.force_rewarded_product = False

    @api.onchange("reward_product_id")
    def _onchange_reward_product_multiple_of(self):
        """We need this to ensure some filters"""
        if self.reward_type == "multiple_of":
            self.discount_product_id = self.reward_product_id

    def write(self, vals):
        """Add context to avoid writing discount products"""
        return super(
            SaleCouponProgram, self.with_context(skip_mapped_multiple_of=True)
        ).write(vals)

    @api.model
    def mapped(self, func):
        """We need to return the proper records when `multiple_of` is set"""
        if (
            not isinstance(func, pycompat.string_types)
            and func != "discount_line_product_id"
        ):
            return super().mapped(func)
        # split normal and multiple_of records
        multiple_of_recs = self.filtered(lambda x: x.reward_type == "multiple_of")
        normal_recs = self - multiple_of_recs
        recs = multiple_of_recs._mapped_func(itemgetter("reward_product_id"))
        if recs and not self.env.context.get("skip_mapped_multiple_of"):
            recs += normal_recs._mapped_func(itemgetter(func))
        else:
            recs = normal_recs._mapped_func(itemgetter(func))
        if isinstance(recs, models.BaseModel):
            # allow feedback to self's prefetch object
            recs = recs.with_prefetch(self._prefetch)
        return recs

    def _check_promo_code(self, order, coupon_code):
        message = super()._check_promo_code(order, coupon_code)
        if message:
            return message
        if (
            self.promo_applicability == "on_current_order"
            and self.reward_type == "multiple_of"
            and (
                not order._is_reward_in_order_lines(self)
                and self.force_rewarded_product
            )
        ):
            message = {
                "error": _(
                    "The reward products should be in the sales order lines "
                    "to apply the discount."
                )
            }
        return message

    def _filter_programs_on_products(self, order):
        valid_programs = super()._filter_programs_on_products(order)
        order_lines = (
            order.order_line.filtered(lambda line: line.product_id)
            - order._get_reward_lines()
        )
        products = order_lines.mapped("product_id")
        products_qties = dict.fromkeys(products, 0)
        for program in self - valid_programs:
            valid_products = program._get_valid_products(products)
            ordered_rule_products_qty = sum(
                products_qties[product] for product in valid_products
            )
            # Avoid program if 1 ordered foo on a program '1 foo, 1 free foo'
            if (
                program.promo_applicability == "on_current_order"
                and program._is_valid_product(program.reward_product_id)
                and program.reward_type == "multiple_of"
            ):
                ordered_rule_products_qty -= program.reward_product_quantity
            if ordered_rule_products_qty >= program.rule_min_quantity:
                valid_programs |= program
        return valid_programs

    def _filter_not_ordered_reward_programs(self, order):
        programs = super()._filter_not_ordered_reward_programs(order)
        for program in self.filtered(
            lambda x: x.reward_type == "multiple_of" and x.force_rewarded_product
        ):
            if not order.order_line.filtered(
                lambda line: line.product_id == program.reward_product_id
            ):
                continue
            programs |= program
        return programs

    def _is_valid_product(self, product):
        if self.force_rewarded_product:
            return product == self.reward_product_id
        return super()._is_valid_product(product)

    def _get_valid_products(self, products):
        if self.force_rewarded_product:
            return products.filtered(lambda x: x == self.reward_product_id)
        return super()._get_valid_products(products)

    def action_view_sales_orders(self):
        """Tracking of multiple of promotions"""
        res = super().action_view_sales_orders()
        if self.reward_type == "multiple_of":
            orders = (
                self.env["sale.order.line"]
                .search(
                    [
                        ("product_id", "=", self.reward_product_id.id),
                        ("is_reward_line", "=", True),
                    ]
                )
                .mapped("order_id")
            )
            res["domain"] = [("id", "in", orders.ids)]
        return res

    def _compute_order_count(self):
        """Multiple programs need a different domain to compute the order count"""
        multiple_of_programs = self.filtered(lambda x: x.reward_type == "multiple_of")
        super(SaleCouponProgram, self - multiple_of_programs)._compute_order_count()
        product_data = self.env["sale.order.line"].read_group(
            [
                (
                    "product_id",
                    "in",
                    multiple_of_programs.mapped("reward_product_id").ids,
                ),
                ("is_reward_line", "=", True),
            ],
            ["product_id"],
            ["product_id"],
        )
        mapped_data = {m["product_id"][0]: m["product_id_count"] for m in product_data}
        for program in multiple_of_programs:
            program.order_count = mapped_data.get(program.reward_product_id.id, 0)
