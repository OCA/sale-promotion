/* Copyright 2023 Tecnativa - Carlos Roca
 * License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl). */

odoo.define("coupon_portal.tour", function (require) {
    "use strict";

    const tour = require("web_tour.tour");

    tour.register(
        "coupon_portal_tour",
        {
            url: "/my",
            test: true,
        },
        [
            {
                trigger: "a[href='/my/coupons']",
                extra_trigger:
                    "a[href='/my/coupons']:has(.badge-secondary:contains('4'))",
            },
            {
                trigger: ".o_portal_search_panel button",
            },
            {
                trigger: "a[href='#program']",
            },
            {
                trigger: "input[name='search']",
                run: "text Nothing found",
            },
            {
                trigger: "button[type='submit']",
                run: "click",
            },
            {
                trigger:
                    "p:contains('There are currently no coupons for your account.')",
            },
            {
                trigger: "input[name='search']",
                run: "text",
            },
            {
                trigger: "button[type='submit']",
                run: "click",
            },
            /* TODO: Test next sentences by clicking on respective filters, can't do it
            because the dropdown was not opened when triggering the button
            #portal_searchbar_filters
            */
            {
                trigger: ".badge-warning",
            },
            {
                trigger: ".badge-danger",
            },
            {
                trigger: ".badge-success",
            },
            {
                trigger: ".badge-info",
            },
        ]
    );
});
