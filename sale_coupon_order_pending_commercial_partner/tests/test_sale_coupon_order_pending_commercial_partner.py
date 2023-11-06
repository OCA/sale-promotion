# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.addons.sale_coupon_commercial_partner_applicability.tests import (
    test_sale_coupon_apply_commercial_partner,
)


class TestSaleCouponApplyCommercialPartner(
    test_sale_coupon_apply_commercial_partner.SaleCouponApplyCommercialPartnerCase
):
    def test_sale_coupon_pending_commercial_partner(self):
        self.assertEqual(
            self.sale.pending_partner_coupon_count,
            1,
            "There should be 1 pending coupon corresponding to another partner "
            "in the commercial entity",
        )
