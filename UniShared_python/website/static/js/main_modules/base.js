'use strict';

require.config({
    baseUrl: window.staticUrl + 'js'
});

require(['lib/live_feed'], function (liveFeed) {
   liveFeed.init();
});