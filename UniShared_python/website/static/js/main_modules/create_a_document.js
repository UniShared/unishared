"use strict";

require.config({
    baseUrl: window.staticUrl + 'js',
    shim: {
        'lib/jquery-ui-timepicker-addon': ['lib/jquery-ui-1.10.1.custom.min'],
        'lib/jquery-ui-sliderAccess': ['lib/jquery-ui-1.10.1.custom.min']
    }
});

require(
    [
        'lib/people_form',
        'lib/validate',
        'lib/document/document_title_form'
    ],
    function (PeopleForm) {

        var $alert = $('#container .alert'),
            $loading = $('.loading'),
            $overlay = $('#overlay'),
            $containerTitle = $('#container_document_title'),
            $container_people = $('#container_people'),
            $nextButton = $('.next_button'),
            $prevButton = $('.prev_button');

        $nextButton.submit(function (ev) {
            var $form_parent = $(this).closest('.form');
            if ($form_parent && $form_parent.find('form').valid() && $form_parent.next('.form').length) {
                $form_parent.fadeOut(500, function () {
                    $(this).next('.form').fadeIn(500);
                });
            }

            ev.returnValue = false;
            ev.preventDefault && ev.preventDefault();
            return false;
        });

        $('.prev_button').click(function () {
            $(this).closest('.form').fadeOut(500, function () {
                $(this).prev().fadeIn(500);
            });
        });

        $.formTitle = $.formTitle || {};
        $containerTitle.on('clickSuggested.unishared', function (event, data) {
            _gaq.push(['_trackEvent', 'Create notes', 'click suggested', data]);
            window.location.href = '/notes/{0}'.format(data);
        });

        var errorHandler = function (data) {
            if (data.status == 500) {
                $nextButton.hide();
                $prevButton.hide();
                $alert.first().show();
                $overlay.hide();
            }
        }

        $container_people.on('submit', function() {
            $alert.hide();

            $loading.show();
            $overlay.show();
        });

        $container_people.on('error', errorHandler);
        $container_people.on('success', function (data) {
            var url = '/notes/',
                resource_id = $('#resource_id').val();

            if (resource_id) {
                url += resource_id;
            }

            window.location = url;
        });
        $.formTitle.errorHandler = errorHandler;

        PeopleForm.attachTo('#container_people', {role: 'cowriters', canClose: false,type: 'notes', resourceId: $('#resource_id').val(), submitLabel: 'Go to my notes!'});

        function backToClassTitle() {
            if ($container_people.is(':visible')) {
                $container_people.fadeOut(500, function () {
                    $('#container_document_title').fadeIn(500);
                });
            }

            $nextButton.show();
            $prevButton.show();
            $alert.first().hide();
        }

        $alert.find('a').click(backToClassTitle);
    });