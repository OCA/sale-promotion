# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import Form, TransactionCase


class SaleCouponApplyCommercialPartnerCase(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.commercial_entity = cls.env["res.partner"].create({"name": "Mrs. Odoo"})
        cls.child_1 = cls.commercial_entity.copy(
            {"name": "Baby Odoo", "parent_id": cls.commercial_entity.id}
        )
        cls.child_2 = cls.child_1.copy({"name": "Odoo Jr."})
        cls.other_partner = cls.commercial_entity.copy({"name": "Mr. OCA"})
        coupon_program_form = Form(
            cls.env["coupon.program"],
            view="coupon.coupon_program_view_coupon_program_form",
        )
        coupon_program_form.name = "Test Apply Commercial Entity"
        cls.code_promotion_program = coupon_program_form.save()
        cls.env["coupon.generate.wizard"].with_context(
            active_id=cls.code_promotion_program.id
        ).create(
            {
                "generation_type": "nbr_customer",
                "partners_domain": f"[('id', 'in', [{cls.child_1.id}])]",
            }
        ).generate_coupon()
        cls.coupon = cls.code_promotion_program.coupon_ids
        cls.product_1 = cls.env["product.product"].create(
            {"name": "Test 1", "sale_ok": True, "list_price": 50}
        )
