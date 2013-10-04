'use strict';

require.config({
    baseUrl: window.staticUrl + 'js'
});

require(
    ["lib/live_feed", "lib/lightbox"],
    function (liveFeed) {
        liveFeed.init();
    });