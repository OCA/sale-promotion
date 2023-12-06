# Copyright 2023 Akretion France (http://www.akretion.com)
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from contextlib import contextmanager

from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @contextmanager
    def _clean_patch_method(self, name, method):
        """Context manager to patch a method and revert it after use"""
        self._patch_method(name, method)
        try:
            yield
        finally:
            self._revert_method(name)

    def _do_get_paid_order_lines_with_super_call(self, cls):
        def _get_paid_order_lines_with_super_call(self):
            """Returns the taxes included sale order total amount without "
            "the rewards amount"""
            # This is the method from sale_coupon_delivery:
            # https://github.com/odoo/odoo/blob/14.0/addons/\
            # sale_coupon_delivery/models/sale_order.py#L16
            # But rewritten to call the super() method.
            free_reward_product = (
                self.env["coupon.program"]
                .search([("reward_type", "=", "product")])
                .mapped("discount_line_product_id")
            )
            # This is what should be done in odoo:
            # Always call super, kids
            paid_order_lines = super(cls, self)._get_paid_order_lines()
            return paid_order_lines.filtered(
                lambda x: not x.is_delivery or x.product_id in free_reward_product
            )

        return _get_paid_order_lines_with_super_call

    def _register_hook(self):
        # If sale_coupon_delivery is installed, we need to patch the
        # _get_paid_order_lines method to force it to call super()
        # in order to avoid inheritance breakage.
        if self.env["ir.module.module"].search(
            [("name", "=", "sale_coupon_delivery"), ("state", "=", "installed")]
        ):
            # We need to patch the sale_coupon_delivery sale_order class
            # Look it up in bases
            SaleOrderCouponDelivery = next(
                base
                for base in self.__class__.__bases__
                if base.__module__
                == "odoo.addons.sale_coupon_delivery.models.sale_order"
            )

            # And patch it using the odoo _patch_method method
            SaleOrderCouponDelivery._patch_method(
                "_get_paid_order_lines",
                self._do_get_paid_order_lines_with_super_call(SaleOrderCouponDelivery),
            )

        return super()._register_hook()

    def _get_reward_values_percentage_amount(self, program):
        # Prevent this patch
        # https://github.com/odoo/odoo/commit/03fb134b89c6739e14ed9426930c91d50b25d896
        # from resetting fixed_amount price_unit since programs can be ordered
        def _do_get_applied_programs(self):
            return (
                super(SaleOrder, self)
                ._get_applied_programs()
                .filtered(lambda p: p.discount_type != "fixed_amount")
            )

        with self._clean_patch_method(
            "_get_applied_programs", _do_get_applied_programs
        ):
            return super()._get_reward_values_percentage_amount(program)
