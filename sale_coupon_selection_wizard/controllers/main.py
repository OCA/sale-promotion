# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, fields
from odoo.exceptions import UserError
from odoo.http import Controller, request, route
from odoo.tests import Form


class CouponSelectionWizardController(Controller):
    def _get_order(self, sale_order_id):
        return request.env["sale.order"].browse(int(sale_order_id or 0))

    def _get_pricelist(self, order, pricelist_fallback=False):
        return order.sudo().pricelist_id

    def _coupon_wizard_item(self, item, pricelist):
        return {
            "criteria_id": request.env["sale.coupon.criteria"].browse(
                item.get("criteria_id")
            ),
            "product_id": (
                request.env["product.product"]
                .browse(item.get("product_id"))
                .with_context(pricelist=pricelist.id)
            ),
            "qty_to_add": item.get("qty_to_add", 0),
            "criteria_qty": item.get("criteria_qty", 0),
            "current_order_quantity": item.get("current_order_quantity", 0),
            "repeat_product": item.get("repeat_product", False),
            "optional": item.get("optional", False),
            "rule_min_quantity": item.get("rule_min_quantity", 0),
        }

    def _get_existing_order_line(self, order, product_id):
        return order.sudo().order_line.filtered(
            lambda x: x.product_id == product_id and not x.is_reward_line
        )

    def _check_promo_code(self, order, program_id):
        """Rely on rules to check whether the promo can be applied or not"""
        error = program_id._check_promo_code(order, program_id.promo_code).get("error")
        if error:
            raise UserError(
                _("The promotion can't be applied to this order:\n%s") % error
            )

    @route(
        "/sale_coupon_selection_wizard/configure",
        type="json",
        auth="public",
        methods=["POST"],
    )
    def configure_promotion(self, program_id, **kw):
        program_id = request.env["sale.coupon.program"].browse(int(program_id))
        order = self._get_order(kw.get("sale_order_id"))
        pricelist = self._get_pricelist(order)
        promo_wizard = request.env["coupon.selection.wizard"].create(
            {"order_id": order.id, "coupon_program_id": program_id.id}
        )
        promo_wizard._compute_available_coupon_program_ids()
        (
            mandatory_lines,
            optional_lines,
        ) = promo_wizard.promotion_line_ids._get_program_options(program_id)
        mandatory_program_options = kw.get(
            "mandatory_program_options",
            [l._convert_to_write(l._cache) for l in mandatory_lines],
        )
        optional_program_options = kw.get(
            "optional_program_options",
            [l._convert_to_write(l._cache) for l in optional_lines],
        )
        optional_program_options_map = {}
        if mandatory_program_options:
            mandatory_program_options = [
                self._coupon_wizard_item(i, pricelist)
                for i in mandatory_program_options
            ]
        if optional_program_options:
            optional_program_options = [
                self._coupon_wizard_item(i, pricelist) for i in optional_program_options
            ]
            # Every criteria is mandatory even if the options are configurable
            for option in optional_program_options:
                optional_program_options_map.setdefault(option["criteria_id"], [])
                optional_program_options_map[option["criteria_id"]].append(option)
        optional_reward_lines = program_id.sudo().coupon_multi_gift_ids.filtered(
            lambda x: len(x.reward_product_ids) > 1
        )
        common_reward_lines = (
            program_id.sudo().coupon_multi_gift_ids - optional_reward_lines
        )
        return request.env["ir.ui.view"].render_template(
            "sale_coupon_selection_wizard.configure",
            {
                "program": program_id,
                "mandatory_program_options": mandatory_program_options,
                "optional_program_options_map": optional_program_options_map,
                "optional_reward_lines": optional_reward_lines,
                "common_reward_lines": common_reward_lines,
                "pricelist": pricelist,
                "currency_id": pricelist.currency_id,
            },
        )

    def _try_to_apply_promotion(
        self, program_id, sale_order_id, promotion_lines, reward_line_options, **kw
    ):
        """Wrapped method"""
        order = self._get_order(sale_order_id).sudo()
        program_id = request.env["sale.coupon.program"].browse(int(program_id)).sudo()
        sale_form = Form(order)
        for product, qty in promotion_lines.items():
            if not qty:
                continue
            product = request.env["product.product"].browse(int(product))
            order_line = fields.first(self._get_existing_order_line(order, product))
            if order_line:
                index = order.order_line.ids.index(order_line.id)
                with sale_form.order_line.edit(index) as line_form:
                    line_form.product_uom_qty += qty
            else:
                with sale_form.order_line.new() as line_form:
                    line_form.product_id = product
                    line_form.product_uom_qty = qty
        reward_line_options = reward_line_options or {}
        reward_line_options = {
            int(reward): int(option) for reward, option in reward_line_options.items()
        }
        # We don't want to apply the changes to the sales order yet, but we need to
        # simulate that the promo is applicable first.
        new_sale = (
            request.env["sale.order"]
            .sudo()
            .new(sale_form._values_to_save(all_fields=True))
        )
        # Force company, otherwise defaults apply
        new_sale.company_id = order.company_id
        # It's going to raise an exception if the program isn't applicable anyway
        error = (
            program_id.sudo()
            ._check_promo_code(new_sale, program_id.promo_code)
            .get("error")
        )
        return error, sale_form, program_id

    def _apply_promotion(self, order, program_id, reward_line_options):
        order = order.with_context(
            reward_line_options=reward_line_options,
            selection_wizard_program=program_id.id,
        )
        if program_id.promo_code_usage == "code_needed":
            request.env["sale.coupon.apply.code"].sudo().apply_coupon(
                order, program_id.promo_code
            )
        else:
            # This context ensures our selection priority
            order.recompute_coupon_lines()
            if program_id not in order.no_code_promo_program_ids:
                return False
        return True

    @route(
        "/sale_coupon_selection_wizard/apply",
        type="json",
        auth="public",
        methods=["POST"],
    )
    def apply_promotion(
        self, program_id, sale_order_id, promotion_lines, reward_line_options, **kw
    ):
        """Backend controller that wraps common methods"""
        # Ensure we provide a dictionary with ids as integers
        reward_line_options = {int(x): int(y) for x, y in reward_line_options.items()}
        error, sale_form, program = self._try_to_apply_promotion(
            program_id, sale_order_id, promotion_lines, reward_line_options, **kw
        )
        if error:
            raise UserError(
                _("The promotion can't be applied to this order:\n%s") % error
            )
        # Once checked write the new lines and force the code if the promo has one
        order = sale_form.save()
        promo_applied = self._apply_promotion(order, program, reward_line_options)
        if not promo_applied:
            raise UserError(_("This promotion can't be applied to this order"))
