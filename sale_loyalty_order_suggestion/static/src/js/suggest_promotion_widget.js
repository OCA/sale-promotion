odoo.define("sale_coupon_order_suggestion.suggest_promotion", function(require) {
    "use strict";

    const Widget = require("web.Widget");
    const widget_registry = require("web.widget_registry");

    const SuggestPromotionWidget = Widget.extend({
        template: "sale_coupon_order_suggestion.suggestPromotion",
        events: _.extend({}, Widget.prototype.events, {
            "click .fa-gift": "_onClickButton",
        }),

        /**
         * @override
         * @param {Widget|null} parent
         * @param {Object} params
         */
        init: function(parent, params) {
            this.data = params.data;
            this._super(parent);
        },

        updateState: function(state) {
            const candidate = state.data[this.getParent().currentRow];
            if (candidate) {
                this.data = candidate.data;
                this.renderElement();
            }
        },

        _onClickButton: function() {
            // When it's a new line, we can't rely on a line id for the wizard, but
            // we can provide the proper element to find the and restrict the proper
            // rewards.
            this.$el.find(".fa-gift").prop("special_click", true);
            var attrs = {
                name: "action_open_promotions_wizard",
                class: "btn btn-secondary",
                string: "Add a promotion",
                type: "object",
                states: "draft,sent,sale",
                context: {
                    active_id: this.data.order_id.res_id,
                    default_order_id: this.data.order_id.res_id,
                    product_id: this.data.product_id.res_id,
                },
                options: {},
            };
            var record = this.data.order_id;
            this.trigger_up("button_clicked", {
                attrs: attrs,
                record: record,
            });
        },
    });

    widget_registry.add("suggest_promotion_widget", SuggestPromotionWidget);

    return SuggestPromotionWidget;
});
