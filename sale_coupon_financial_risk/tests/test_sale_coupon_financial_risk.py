# Copyright 2023 Tecnativa - Stefan Ungureanu
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import Form, common


class TestSaleCouponFinancialRisk(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.groups_id |= cls.env.ref(
            "account_financial_risk.group_account_financial_risk_manager"
        )
        cls.partner = cls.env["res.partner"].create(
            {"name": "Partner", "email": "demo@demo.com"}
        )
        cls.product = cls.env["product.product"].create({"name": "Product"})
        cls.coupon_program = cls._create_coupon_program(cls)
        cls.order = cls._create_sale_order(cls)
        cls.order.recompute_coupon_lines()
        cls.cron_mail_scheduler = cls.env.ref("mail.ir_cron_mail_scheduler_action")
        cls.mail_model = cls.env["mail.mail"].sudo()
        cls.mail_message_model = cls.env["mail.message"].sudo()

    def _create_coupon_program(self):
        coupon_program_form = Form(
            self.env["sale.coupon.program"],
            view="sale_coupon.sale_coupon_program_view_promo_program_form",
        )
        coupon_program_form.name = "Coupon program"
        coupon_program_form.rule_products_domain = [("id", "=", self.product.id)]
        coupon_program_form.rule_min_quantity = 1
        coupon_program_form.promo_applicability = "on_next_order"
        coupon_program_form.discount_type = "fixed_amount"
        coupon_program_form.discount_fixed_amount = 10
        coupon_program_form.promo_code_usage = "no_code_needed"
        return coupon_program_form.save()

    def _create_sale_order(self):
        sale_form = Form(self.env["sale.order"])
        sale_form.partner_id = self.partner
        with sale_form.order_line.new() as line_form:
            line_form.product_id = self.product
            line_form.product_uom_qty = 3
            line_form.price_unit = 100
        return sale_form.save()

    def test_sale_coupon_risk_exceeded_bypassed(self):
        self.mail_message_model.search([]).unlink()
        self.mail_model.search([]).write({"auto_delete": False})
        self.partner.risk_sale_order_include = True
        self.partner.credit_limit = 99
        wiz_dic = self.order.action_confirm()
        wiz = self.env[wiz_dic["res_model"]].browse(wiz_dic["res_id"])
        wiz.button_continue()
        message = self.env["mail.message"].search(
            [
                ("model", "=", "sale.coupon"),
                ("res_id", "=", self.order.generated_coupon_ids[0].id),
            ]
        )
        self.assertEqual(len(message), 1)

    def test_sale_coupon_risk_exceeded_no_bypassed(self):
        self.mail_message_model.search([]).unlink()
        self.mail_model.search([]).write({"auto_delete": False})
        self.partner.risk_sale_order_include = True
        self.partner.credit_limit = 99
        wiz_dic = self.order.action_confirm()
        self.env[wiz_dic["res_model"]].browse(wiz_dic["res_id"])
        message = self.env["mail.message"].search(
            [
                ("model", "=", "sale.coupon"),
                ("res_id", "=", self.order.generated_coupon_ids[0].id),
            ]
        )
        self.assertEqual(len(message), 0)
