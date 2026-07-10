# Copyright 2021 Tecnativa - Carlos Roca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
import io

from PIL import Image

from odoo.tests import tagged
from odoo.tests.common import HttpCase


@tagged("post_install", "-at_install")
class WebsiteSaleHttpCase(HttpCase):
    def setUp(self):
        super().setUp()
        # Ensure portal user exists for the tour login
        portal_user = self.env.ref("base.demo_user0", raise_if_not_found=False)
        if not portal_user:
            self.env["res.users"].create(
                {
                    "name": "Portal",
                    "login": "portal",
                    "password": "portal",
                    "group_ids": [(6, 0, [self.env.ref("base.group_portal").id])],
                }
            )
        else:
            portal_user.write({"password": "portal"})
        # Creation of generic test banner
        f = io.BytesIO()
        Image.new("RGB", (800, 500), "#FF0000").save(f, "JPEG")
        f.seek(0)
        image = base64.b64encode(f.read())
        self.promo_published = self.env["loyalty.program"].create(
            {
                "program_type": "promotion",
                "name": "Test 01",
                "is_published": True,
                "public_name": "<p>10% discount</p>",
                "image_1920": image,
            }
        )
        self.promo_not_published = self.env["loyalty.program"].create(
            {
                "program_type": "promotion",
                "name": "Test 02",
                "is_published": False,
                "public_name": "<p>Promo not published</p>",
                "image_1920": image,
            }
        )

    def test_ui(self):
        self.start_tour(
            "/promotions",
            "website_sale_loyalty_page_portal",
            login="portal",
        )

    def test_promotions_route(self):
        res = self.url_open("/promotions")
        self.assertEqual(res.status_code, 200)
