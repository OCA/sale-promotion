# Copyright 2021 Camptocamp SA (https://www.camptocamp.com).
# @author Iván Todorovich <ivan.todorovich@camptocamp.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_applicable_programs(self):
        # OVERRIDE to add the handle_rule_date_field context key.
        # Original method is filtering out rules with a hardcoded domain.
        # We alter this hardcoded domain in :meth:`coupon_program.search`
        self_ctx = self.with_context(coupon_rule_commitment_date=self.commitment_date)
        res = super(SaleOrder, self_ctx)._get_applicable_programs()
        return res

    def _get_applicable_no_code_promo_program(self):
        # OVERRIDE to add the handle_rule_date_field context key.
        # Original method is filtering out rules with a hardcoded domain.
        # We alter this hardcoded domain in :meth:`coupon_program.search`
        self_ctx = self.with_context(coupon_rule_commitment_date=self.commitment_date)
        return super(SaleOrder, self_ctx)._get_applicable_no_code_promo_program()
