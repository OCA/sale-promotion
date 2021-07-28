odoo.define("sale_coupon_selection_wizard.CouponSelectionMixin", function() {
    "use strict";

    var CouponSelectionMixin = {
        events: {
            "change .js_promotion_item_quantity": "_onchange_quantity",
            "click button.csw_add_quantity, button.csw_remove_quantity":
                "_onclick_add_or_remove",
            "click button.o_coupon_selection_wizard_apply": "apply_promotion",
            "click div.csw_optional_reward": "_onclick_choose_reward",
        },
        /**
         * This is overridden to allow catching the "select" event on the
         * promotion select field.
         *
         * @override
         * @private
         */
        _onFieldChanged: function(event) {
            this._super.apply(this, arguments);
            var self = this;
            var program_id = event.data.changes.coupon_program_id.id;
            // Check to prevent traceback when emptying the field
            if (!program_id) {
                return;
            }
            this._configure_promotion(program_id).then(function() {
                self.renderer.renderPromotion(self.renderer.promotionHtml);
            });
        },
        /**
         * Renders the components needed for the promotion
         *
         * @param {integer} program_id
         * @returns {Promise}
         */
        _configure_promotion: function(program_id) {
            var self = this;
            var initialProgram = this.initialState.data.coupon_program_id;
            var changed = initialProgram && initialProgram.data.id !== program_id;
            var promotion_lines = this.renderer.state.data.promotion_line_ids.data;
            var sale_order_id = this.renderer.state.data.order_id.data.id;
            var criteria_repeat_mandatory = Object.entries(
                promotion_lines.reduce((result, current) => {
                    if (current.data.repeat_product) {
                        result[current.data.criteria_id.data.id] =
                            result[current.data.criteria_id.data.id] || 0;
                        result[current.data.criteria_id.data.id] += 1;
                    }
                    return result;
                }, {})
            )
                .filter(criteria => criteria[1] > 1)
                .map(function(criteria) {
                    return parseInt(criteria[0], 10);
                });
            // We include optional criterias with a single product
            var mandatory_promotion_lines = promotion_lines.filter(
                line =>
                    line.data.program_id.data.id === program_id &&
                    (!line.data.repeat_product ||
                        !criteria_repeat_mandatory.includes(
                            line.data.criteria_id.data.id
                        ))
            );
            var optional_promotion_lines = promotion_lines.filter(
                line =>
                    line.data.program_id.data.id === program_id &&
                    line.data.repeat_product &&
                    criteria_repeat_mandatory.includes(line.data.criteria_id.data.id)
            );
            return this._rpc({
                route: "/sale_coupon_selection_wizard/configure",
                params: {
                    program_id: program_id,
                    mandatory_program_options: changed
                        ? []
                        : this._get_program_options(mandatory_promotion_lines),
                    optional_program_options: changed
                        ? []
                        : this._get_program_options(optional_promotion_lines),
                    sale_order_id: sale_order_id,
                },
            }).then(function(configurator) {
                self.renderer.promotionHtml = configurator;
            });
        },
        /**
         * When the quantity changes, apply some logic to help the user checking if
         * the promotion can be applied or not.
         *
         * @param {InputEvent} ev
         */
        _onchange_quantity: function(ev) {
            var $row = $(ev.currentTarget).closest(".optional_criteria_row");
            var $needed_qty_span = $row.find(".csw_criteria_needed_qty");
            var $criteria_icon = $row.find(".csw_criteria_icon");
            var $row_add_buttons = $row.find(".csw_add_quantity");
            var $inputs = $row.find("input");
            var needed_qty = parseInt($needed_qty_span.data("qty"), 10);
            var current_row_qty = 0;
            _.each($inputs, function(inp) {
                current_row_qty += parseInt(inp.value, 10);
            });
            needed_qty = Math.max(needed_qty - current_row_qty, 0);
            if (!needed_qty) {
                $needed_qty_span.parent().addClass("d-none");
                $row_add_buttons.attr("disabled", "disabled");
                $criteria_icon.removeClass(["fa-sun-o", "text-warning"]);
                $criteria_icon.addClass(["fa-certificate", "text-success"]);
                $inputs
                    .filter(function() {
                        return this.value !== "0";
                    })
                    .closest(".card")
                    .addClass("border-success");
            } else {
                $needed_qty_span.parent().removeClass("d-none");
                $row_add_buttons.removeAttr("disabled");
                $criteria_icon.removeClass(["fa-certificate", "text-success"]);
                $criteria_icon.addClass(["fa-sun-o", "text-warning"]);
                $inputs.closest(".card").removeClass("border-success");
                $needed_qty_span.text(needed_qty);
            }
        },
        /**
         * Buttons circuitry
         *
         * @param {InputEvent} ev
         */
        _onclick_add_or_remove: function(ev) {
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
            return false;
        },
        /**
         * Reward card click circuitry
         *
         * @param {InputEvent} ev
         */
        _onclick_choose_reward: function(ev) {
            ev.preventDefault();
            var $input = $(ev.currentTarget).find("input");
            var $input_siblings = $(ev.currentTarget.closest(".row")).find(
                "input[name='" + $input.attr("name") + "']"
            );
            _.each($input_siblings, function($sibling) {
                $($sibling)
                    .closest(".card")
                    .removeClass("bg-success");
            });
            $input.prop("checked", true);
            $(ev.currentTarget).addClass("bg-success");
        },
        /**
         * Communicate the form options to the controller. An object with product id
         * key and quantity as value is passed to try to apply them to the order and
         * check if the selected coupon can be applied.
         *
         * @returns {Promise}
         */
        apply_promotion: function() {
            var _this = this;
            var $modal = this.$el;
            var $wizard_inputs = $modal.find("input.js_promotion_item_quantity");
            var $reward_options = $modal.find("input.reward_optional_input:checked");
            var promotion_values = {};
            // Group by products then clean 0 keys
            _.each($wizard_inputs, function($input) {
                var product_id = $input.dataset.product_id;
                promotion_values[product_id] = promotion_values[product_id] || 0;
                promotion_values[product_id] +=
                    ($input.value && parseInt($input.value, 10)) || 0;
            });
            var reward_line_options = {};
            _.each($reward_options, function($input) {
                var reward_id = $input.name.replace("reward-", "");
                reward_line_options[reward_id] = $input.value;
            });
            return this._rpc({
                route: "/sale_coupon_selection_wizard/apply",
                params: {
                    program_id: _this.renderer.state.data.coupon_program_id.data.id,
                    sale_order_id: _this.renderer.state.data.order_id.data.id,
                    promotion_lines: promotion_values,
                    reward_line_options: reward_line_options,
                },
            }).then(function() {
                _this.do_action({type: "ir.actions.act_window_close"});
            });
        },
        /**
         * Prepare option line for renderer controller
         *
         * @private
         * @param {Object} line - promotion line item
         * @returns {Object} promotion line formatted for controller
         */
        _prepare_option_line: function(line) {
            return {
                criteria_id: line.criteria_id.data.id,
                product_id: line.product_id.data.id,
                qty_to_add: line.qty_to_add,
                current_order_quantity: line.current_order_quantity,
                repeat_product: line.repeat_product,
                criteria_qty: line.criteria_qty,
                rule_min_quantity: line.rule_min_quantity,
                optional: line.optional,
            };
        },
        /**
         * Return the mandatory products altogether
         *
         * @private
         * @param {Array} promotion_line_ids
         * @returns {Array} result
         */
        _get_program_options: function(promotion_line_ids) {
            if (!promotion_line_ids || promotion_line_ids.length === 0) {
                return [];
            }
            var _this = this;
            var result = [];
            _.each(promotion_line_ids, function(line) {
                result.push(_this._prepare_option_line(line.data));
            });
            return result;
        },
        /**
         * We need to override the default click behavior for our "Add" button
         * because there is a possibility that this product has optional products.
         * If so, we need to display an extra modal to choose the options.
         *
         * @override
         */
        _onButtonClicked: function(event) {
            if (event.stopPropagation) {
                event.stopPropagation();
            }
            var attrs = event.data.attrs;
            if (attrs.special === "cancel") {
                this._super.apply(this, arguments);
            } else if (
                !this.$el
                    .parents(".modal")
                    .find(".o_coupon_selection_wizard_apply")
                    .hasClass("disabled")
            ) {
                this.apply_promotion();
            }
        },
    };
    return CouponSelectionMixin;
});
