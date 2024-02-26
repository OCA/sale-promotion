/* Copyright 2021 Tecnativa - David Vidal
 * License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl). */
odoo.define("website_sale_loyalty_suggestion_wizard", function (require) {
    "use strict";

    const CouponSelectionMixin = require("website_sale_loyalty_suggestion_wizard.CouponSelectionMixin");
    const publicWidget = require("web.public.widget");
    const websiteSale = require("website_sale.website_sale");

    publicWidget.registry.WebsiteSaleLoyaltySuggestionWizard =
        publicWidget.Widget.extend(CouponSelectionMixin, {
            selector: "#o_promo_configure",
            events: Object.assign({}, CouponSelectionMixin.events || {}, {
                "click .o_coupon_selection_wizard_apply": "apply_promotion",
            }),
            /**
             * @override
             */
            start: function () {
                const def = this._super.apply(this, arguments);
                this.program_id = $("span.js_promotion_change")
                    .first()
                    .data().promotionId;
                this.website_sale_order = $("span.website_sale_order_id")
                    .first()
                    .data().orderId;
                $("span.js_promotion_change").trigger("change");
                return def;
            },
            /**
             * Communicate the form options to the controller. An object with product id
             * key and quantity as value is passed to try to apply them to the order and
             * check if the selected coupon can be applied.
             *
             * @returns {Promise}
             */
            apply_promotion: async function () {
                const $modal = this.$el;
                const $wizard_inputs = $modal.find("input.js_promotion_item_quantity");
                const $reward_options = $modal.find(
                    "input.reward_optional_input:checked"
                );
                const $cardBodyContainer = $reward_options.closest(
                    "div.csw_optional_reward"
                );
                const $reward_selected_product =
                    $cardBodyContainer.find(".bg-info input");
                var promotion_values = {};
                $wizard_inputs.each(function () {
                    const product_id = this.dataset.product_id;
                    promotion_values[product_id] =
                        (promotion_values[product_id] || 0) +
                        (parseInt(this.value, 10) || 0);
                });
                var reward_line_options = {
                    reward_id: $reward_options.val(),
                    selected_product_ids: $reward_selected_product
                        .map(function () {
                            return this.value;
                        })
                        .get(),
                };
                await this._rpc({
                    route: "/website_sale_loyalty_suggestion_wizard/apply",
                    params: {
                        program_id: this.program_id,
                        sale_order_id: this.website_sale_order,
                        promotion_lines: promotion_values,
                        reward_line_options: reward_line_options,
                    },
                });
                $("#o_promo_configure_modal").modal("hide");
                window.location = "/shop/cart";
            },
        });

    websiteSale.websiteSaleCart.include({
        /**
         * Opens the promotion modal by default when the cart is reloaded
         * @override
         */
        start: function () {
            const def = this._super.apply(this, arguments);
            return def.then(() => {
                $("#o_promo_configure_modal").modal("show");
            });
        },
    });
});
