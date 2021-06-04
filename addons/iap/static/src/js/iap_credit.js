neoziv.define('iap.redirect_neoziv_credit_widget', function(require) {
"use strict";

var AbstractAction = require('web.AbstractAction');
var core = require('web.core');


var IapneozivCreditRedirect = AbstractAction.extend({
    template: 'iap.redirect_to_neoziv_credit',
    events : {
        "click .redirect_confirm" : "neoziv_redirect",
    },
    init: function (parent, action) {
        this._super(parent, action);
        this.url = action.params.url;
    },

    neoziv_redirect: function () {
        window.open(this.url, '_blank');
        this.do_action({type: 'ir.actions.act_window_close'});
        // framework.redirect(this.url);
    },

});
core.action_registry.add('iap_neoziv_credit_redirect', IapneozivCreditRedirect);
});
