/* Copyright 2020 Jairo Llopis - Tecnativa
 * License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl). */

import {registry} from "@web/core/registry";

registry.category("web_tour.tours").add("website_sale_loyalty_page_portal", {
    test: true,
    url: "/promotions",
    steps: () => [
        {
            trigger:
                ".card:has(.card-body:has(.card-text:contains('10% discount'))) .card-img-top",
            run: "click",
        },
        {
            trigger: "button.btn-close",
            run: "click",
        },
        {
            trigger:
                ".card:not(:has(.card-body:has(.card-text:contains('Promo not published'))))",
        },
    ],
});
