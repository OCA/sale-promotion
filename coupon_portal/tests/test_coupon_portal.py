# Copyright 2023 Tecnativa - Carlos Roca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import Form, common


@common.tagged("post_install", "-at_install")
class TestCouponPortal(common.HttpCase):
    def setUp(self):
        super().setUp()
        product_form = Form(self.env["product.product"])
        product_form.name = "Product Test"
        product_form.type = "consu"
        self.product = product_form.save()
        program_form = Form(
            self.env["coupon.program"],
            view="coupon.coupon_program_view_promo_program_form",
        )
        program_form.name = "Test promotion"
        self.program = program_form.save()
        generate_coupon_form = Form(
            self.env["coupon.generate.wizard"].with_context(active_id=self.program.id)
        )
        generate_coupon_form.generation_type = "nbr_customer"
        generate_coupon_form.partners_domain = (
            "[['id','=',%s]]" % self.env.ref("base.partner_demo_portal").id
        )
        generate_coupon_wiz = generate_coupon_form.save()
        generate_coupon_wiz.generate_coupon()
        generate_coupon_wiz.generate_coupon()
        generate_coupon_wiz.generate_coupon()
        generate_coupon_wiz.generate_coupon()
        # Change state of 3 coupons.
        self.program.coupon_ids.filtered(lambda c: c.state == "sent")[
            0
        ].state = "reserved"
        self.program.coupon_ids.filtered(lambda c: c.state == "sent")[0].state = "used"
        self.program.coupon_ids.filtered(lambda c: c.state == "sent")[
            0
        ].state = "expired"
        self.program.coupon_ids.filtered(lambda c: c.state == "sent")[0].state = "new"
        # Create one more coupon for other partner
        generate_coupon_form = Form(
            self.env["coupon.generate.wizard"].with_context(active_id=self.program.id)
        )
        generate_coupon_form.generation_type = "nbr_customer"
        generate_coupon_form.partners_domain = (
            "[['id','=',%s]]" % self.env.ref("base.partner_admin").id
        )
        generate_coupon_wiz = generate_coupon_form.save()
        generate_coupon_wiz.generate_coupon()

    def test_portal_interface(self):
        # Then check for each user that the state at portal is valid
        self.start_tour("/", "coupon_portal_tour", login="portal")
