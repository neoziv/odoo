neoziv.define('mail_bot/static/tests/helpers/mock_server.js', function (require) {
"use strict";

const MockServer = require('web.MockServer');

MockServer.include({
    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * @override
     */
    async _performRpc(route, args) {
        if (args.model === 'mail.channel' && args.method === 'init_neozivbot') {
            return this._mockMailChannelInitneozivBot();
        }
        return this._super(...arguments);
    },

    //--------------------------------------------------------------------------
    // Private Mocked Methods
    //--------------------------------------------------------------------------

    /**
     * Simulates `init_neozivbot` on `mail.channel`.
     *
     * @private
     */
    _mockMailChannelInitneozivBot() {
        // TODO implement this mock task-2300480
        // and improve test "neozivBot initialized after 2 minutes"
    },
});

});
