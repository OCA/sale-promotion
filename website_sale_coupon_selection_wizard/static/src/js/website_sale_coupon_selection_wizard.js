/* Copyright 2021 Tecnativa - David Vidal
 * License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl). */
odoo.define("website_sale_coupon_selection_wizard", function (require) {
    "use strict";

    const CouponSelectionMixin = require("sale_coupon_selection_wizard.CouponSelectionMixin");
    const publicWidget = require("web.public.widget");
    const websiteSale = require("website_sale.website_sale");

    publicWidget.registry.WebsiteSaleCouponWizard = publicWidget.Widget.extend(
        CouponSelectionMixin,
        {
            selector: "#o_promo_configure",
            events: Object.assign({}, CouponSelectionMixin.events || {}, {
                "change span.js_promotion_change": "_onChangePromotion",
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
             * @private
             */
            _onChangePromotion: function () {
                this._configure_promotion_cart(
                    this.program_id,
                    this.website_sale_order
                );
            },
            /**
             * Renders the components needed for the promotion
             *
             * @param {integer} program_id
             * @param {integer} website_sale_order
             * @returns {Promise}
             */
            _configure_promotion_cart: async function (program_id, website_sale_order) {
                const configurator = await this._rpc({
                    route: "/sale_coupon_selection_wizard/configure",
                    params: {
                        program_id: program_id,
                        sale_order_id: website_sale_order,
                    },
                });
                const [$o_promo_config_body] = this.$el.find("#o_promo_config_body");
                $o_promo_config_body.insertAdjacentHTML("beforeend", configurator);
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
                var promotion_values = {};
                // Group by products then clean 0 keys
                for (const $input of $wizard_inputs) {
                    const product_id = $input.dataset.product_id;
                    promotion_values[product_id] = promotion_values[product_id] || 0;
                    promotion_values[product_id] +=
                        ($input.value && parseInt($input.value, 10)) || 0;
                }
                var reward_line_options = {};
                for (const $input of $reward_options) {
                    const reward_id = $input.name.replace("reward-", "");
                    reward_line_options[reward_id] = $input.value;
                }
                await this._rpc({
                    route: "/website_sale_coupon_selection_wizard/apply",
                    params: {
                        program_id: this.program_id,
                        sale_order_id: this.website_sale_order,
                        promotion_lines: promotion_values,
                        reward_line_options: reward_line_options,
                        website_wizard: true,
                    },
                });
                $("#o_promo_configure_modal").modal("hide");
                window.location = "/shop/cart";
            },
        }
    );

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
