odoo.define("website_sale_loyalty_suggestion_wizard.CouponSelectionMixin", function () {
    "use strict";

    var CouponSelectionMixin = {
        events: {
            "change .js_promotion_item_quantity": "_onchange_quantity",
            "click button.csw_add_quantity, button.csw_remove_quantity":
                "_onclick_add_or_remove",
            "click div.csw_optional_reward": "_onclick_choose_reward",
            "click div.csw_optional_product": "_onclick_choose_product",
        },
        /**
         * When the quantity changes, apply some logic to help the user checking if
         * the promotion can be applied or not.
         *
         * @param {InputEvent} ev
         */
        _onchange_quantity: function (ev) {
            var $row = $(ev.currentTarget).closest(".row.pl-3.pr-3");
            var $needed_qty_span = $row.find(".csw_criteria_needed_qty");
            var $criteria_icon = $row.find(".csw_criteria_icon");
            var $row_add_buttons = $row.find(".csw_add_quantity");
            var $inputs = $row.find("input");
            var needed_qty = parseInt($needed_qty_span.data("qty"), 10);
            var current_row_qty = 0;
            _.each($inputs, function (inp) {
                current_row_qty += parseInt(inp.value, 10);
            });
            needed_qty = Math.max(needed_qty - current_row_qty, 0);
            if (needed_qty) {
                $needed_qty_span.parent().removeClass("d-none");
                $row_add_buttons.removeAttr("disabled");
                $criteria_icon.removeClass(["fa-certificate", "text-success"]);
                $criteria_icon.addClass(["fa-sun-o", "text-warning"]);
                $inputs.closest(".card").removeClass("border-success");
                $needed_qty_span.text(needed_qty);
            } else {
                $needed_qty_span.parent().addClass("d-none");
                $row_add_buttons.attr("disabled", "disabled");
                $criteria_icon.removeClass(["fa-sun-o", "text-warning"]);
                $criteria_icon.addClass(["fa-certificate", "text-success"]);
                $inputs
                    .filter(function () {
                        return this.value !== "0";
                    })
                    .closest(".card")
                    .addClass("border-success");
            }
        },
        /**
         * Buttons circuitry
         *
         * @param {InputEvent} ev
         */
        _onclick_add_or_remove: function (ev) {
            ev.preventDefault();
            var $button = $(ev.currentTarget);
            var $input = $button.closest(".input-group").find("input");
            var min = parseFloat($input.attr("min") || 0);
            var max = parseFloat($input.attr("max") || Infinity);
            var previousQty = parseFloat($input.val() || 0, 10);
            var quantity = ($button.has(".fa-minus").length ? -1 : 1) + previousQty;
            var newQty = quantity > min ? (quantity < max ? quantity : max) : min;
            if (newQty !== previousQty) {
                $input.val(newQty).trigger("change");
            }
        },
        /**
         * Reward card click circuitry
         *
         * @param {InputEvent} ev
         */
        _onclick_choose_reward: function (ev) {
            ev.preventDefault();
            var $input = $(ev.currentTarget).find("input[name='reward']");
            var $input_siblings = $(ev.currentTarget.closest(".row")).find(
                "input[name='reward']"
            );
            _.each($input_siblings, function ($sibling) {
                $($sibling)
                    .closest(".csw_optional_reward")
                    .not(ev.currentTarget)
                    .find(".bg-info")
                    .removeClass("bg-info");
                $($sibling).closest(".csw_optional_reward").removeClass("bg-success");
            });
            $input.prop("checked", true);
            $(ev.currentTarget).addClass("bg-success");
            this._choose_default_products($(ev.currentTarget));
        },

        _choose_default_products: async function ($target) {
            const defaults = await this._rpc({
                route: "/website_sale_loyalty_suggestion_wizard/get_defaults",
            });
            for (var def of defaults) {
                const $input = $target.find(
                    "input.reward_product_input[value='" + def + "']"
                );
                var group = $input.attr("name");
                var $input_siblings = $target.find(
                    "input[name='" + group + "']:checked"
                );
                if (!$input_siblings.length) {
                    $input.prop("checked", true);
                    $input.closest(".csw_optional_product").addClass("bg-info");
                }
            }
            console.log(defaults);
        },
        /**
         * Reward product card click circuitry
         *
         * @param {InputEvent} ev
         */
        _onclick_choose_product: function (ev) {
            ev.preventDefault();
            var $input = $(ev.currentTarget).find("input.reward_product_input");
            var group = $input.attr("name");
            var $input_siblings = $(ev.currentTarget.closest(".card-body")).find(
                "input[name='" + group + "']"
            );
            _.each($input_siblings, function ($sibling) {
                $($sibling).closest(".card").removeClass("bg-info");
            });
            $input.prop("checked", true);
            $(ev.currentTarget).addClass("bg-info");
        },
    };
    return CouponSelectionMixin;
});
