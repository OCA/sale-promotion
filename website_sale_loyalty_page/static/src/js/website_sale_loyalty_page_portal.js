/* Copyright 2020 Jairo Llopis - Tecnativa
 * License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl). */

odoo.define("website_sale_loyalty_page.tour_portal", function (require) {
    "use strict";

    const tour = require("web_tour.tour");

    tour.register(
        "website_sale_loyalty_page_portal",
        {
            url: "/promotions",
            test: true,
        },
        [
            {
                trigger:
                    ".card:has(.card-body:has(.card-text:contains('10% discount'))) .card-img-top",
            },
            {
                trigger: "button.btn-close",
                extra_trigger: ".show:has(.modal-body:has(img))",
            },
            {
                trigger: "a[href='/shop']",
                extra_trigger:
                    ".card:not(:has(.card-body:has(.card-text:contains('Promo not published'))))",
            },
        ]
    );
});
