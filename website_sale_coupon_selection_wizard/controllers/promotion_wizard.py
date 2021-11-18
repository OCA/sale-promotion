# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _
from odoo.http import request, route

from odoo.addons.sale_coupon_selection_wizard.controllers.main import (
    CouponSelectionWizardController,
)


class CouponSelectionWizardController(CouponSelectionWizardController):
    @route(
        "/website_sale_coupon_selection_wizard/apply",
        type="json",
        auth="public",
        methods=["POST"],
    )
    def apply_promotion_public(
        self, program_id, sale_order_id, promotion_lines, reward_line_options, **kw
    ):
        """Frontend controller that wraps common methods and handles errors properly"""
        error, sale_form, program = self._try_to_apply_promotion(
            program_id, sale_order_id, promotion_lines, reward_line_options, **kw
        )
        if error:
            request.session["error_promo_code"] = error
            return
        # Once checked write the new lines and force the code if the promo has one
        order = sale_form.save()
        promo_applied = self._apply_promotion(order, program, reward_line_options)
        if not promo_applied:
            request.session["error_promo_code"] = _(
                "This promotion can't be applied to this order"
            )
        request.session.pop("promotion_id", None)
        request.session.pop("error_promo_code", None)

    @route(website=True)
    def configure_promotion(self, program_id, **kw):
        if not self._get_order(kw.get("sale_order_id")):
            kw["sale_order_id"] = request.website.sale_get_order(force_create=True)
        return super().configure_promotion(program_id, **kw)
