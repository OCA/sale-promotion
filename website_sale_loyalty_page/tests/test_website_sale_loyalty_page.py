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
