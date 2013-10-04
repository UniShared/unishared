/**
 * Created with IntelliJ IDEA.
 * User: arnaud
 * Date: 19/02/13
 * Time: 22:17
 * To change this template use File | Settings | File Templates.
 */

require.config({
    baseUrl: window.staticUrl + 'js'
});

define('noteTakingBuddyForm',
    [
        'lib/components/component',
        'lib/core'
    ],
    function (defineComponent) {
        return defineComponent(noteTakingBuddyForm);

        function noteTakingBuddyForm() {
            this.defaultAttrs({
                overlay: $('#overlay'),
                containerPassionatedBySubject: '#container_passionated_by_subject',
                containerNoteTakingFormat: '#container_note_taking_format',
                containerAugmentedDocuments: '#container_augmented_documents',
                containerBehavior: '#container_behavior',
                containerLogin: '#container_login_session',
                containerLive: '#container_live',
                hubLink: '.hub_link',
                formText: '.form_text',
                prevButton: '.prev_button',
                postForm: 'form',
                formIsBound: '#form_is_bound'
            });

            this.after('initialize', function () {
                if(this.select('formIsBound').val() === 'True') {
                    this.attr.overlay.show().find('.loading').show();
                    this.select('postForm').submit();
                }

                this.select('formText').find('a').click($.proxy(this.submitHandler, this));
                this.select('prevButton').click($.proxy(this.backHandler, this));
                this.select('hubLink').click($.proxy(this.pushAnalytics, this, "hub link"));

                this.select('containerLogin').find('h2').text('to meet your note-taking buddies');
                this.select('containerLogin').click($.proxy(this.loginAndSubmit, this));
                this.select('containerPassionatedBySubject').show();
            });

            this.pushAnalytics = function(eventName) {
                window._gaq.push(['_trackEvent', 'Buddies', 'start', eventName]);
            }

            this.submitHandler = function (event) {
                var target = $(event.target).closest('.form_text'),
                data = target.data('value'),
                form = this.select('postForm');

                if(this.select('containerPassionatedBySubject').find(target).length) {
                    form.find('#id_passionated_by_subject').prop('checked', data);
                }
                else if(this.select('containerNoteTakingFormat').find(target).length) {
                    form.find('#id_note_taking_format').val(data);
                }
                else if(this.select('containerAugmentedDocuments').find(target).length) {
                    form.find('#id_augmented_documents').prop('checked', data);
                }
                else if(this.select('containerBehavior').find(target).length) {
                    form.find('#id_behavior').val(data);
                }
                else if(this.select('containerLive').find(target).length) {
                    form.find('#id_live_session').prop('checked', data);
                }

                var $currentForm = target.closest('.form'), $nextForm= $currentForm.next('.form');

                if($nextForm.length) {
                    $currentForm.fadeOut(500, function () { $nextForm.show(); });
                }
                else {
                    this.attr.overlay.show().find('.loading').show();
                    form.submit();
                }
            }

            this.backHandler = function (event) {
                var target = $(event.target),
                $currentForm = target.closest('.form'), $prevForm= $currentForm.prev('.form');

                if($prevForm.length) {
                    $currentForm.fadeOut(500, function () { $prevForm.show(); });
                }

                this.pushAnalytics($currentForm.attr('id') + '_prev_button')
            }

            this.loginAndSubmit = function () {
                this.attr.overlay.show().find('.loading').show();
                window.location.href = $('#login_url').val() + window.location.pathname + encodeURIComponent('?' + this.select('postForm').serialize());

                return false;
            }
        }
    });

require(['noteTakingBuddyForm'], function (noteTakingBuddyForm) {
    $(document).ready(function () {
        noteTakingBuddyForm.attachTo('#container');
    });
})