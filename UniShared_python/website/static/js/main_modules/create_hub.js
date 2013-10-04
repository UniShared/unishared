'use strict';

require.config({
    baseUrl: window.staticUrl + 'js'
});

require(['lib/core', 'lib/validate', 'lib/hub/hub_name_form'], function () {
    var $overlay = $('#overlay'), $alert = $('#alert'), $loading = $('.loading'), $containerHubNameForm = $('#container_hub_name');

    $containerHubNameForm.hubNameForm({
        'successHandler': function (response) {
            if(response) {
                if(response.success && response.success === true) {
                    window.location.href = response.message;
                }
                else {
                    $overlay.hide();
                    $loading.hide();

                    $alert.text(response.message);
                    $alert.addClass('alert-error');
                    $alert.show();
                }
            }
        }
    });

    $containerHubNameForm.on('hub-name-form-submit', function () {
        $alert.hide();
        $loading.show();
        $overlay.show();
    })
});