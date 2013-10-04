/**
 * Created with IntelliJ IDEA.
 * User: arnaud
 * Date: 20/02/13
 * Time: 19:16
 * To change this template use File | Settings | File Templates.
 */

require.config({
    baseUrl: window.staticUrl + 'js'
});

define('noteTakingBuddyResults',
    [
        'lib/components/component',
        'lib/core',
        'lib/activity_feed'
    ],
    function (defineComponent) {
        return defineComponent(noteTakingBuddyResults);

        function noteTakingBuddyResults() {
            this.defaultAttrs({
                activityFeed: '.feed',
                fromHub: null,
                startNotesButton: '#buddies_action_button_start_notes',
                participateNotesButton: '#buddies_action_button_participate_notes',
                findBuddiesButton: '#buddies_action_button_find_buddies_results, #buddies_action_button_find_buddies_no_results',
                hubLink: '.hub_link',
                usersProfiles: '.user',
                removeCowriterButton: '.remove_cowriter',
                profileLink: '.profile_link',
                cowritersSelected: undefined
            });

            this.after('initialize', function () {
                this.initActivityFeed();
                this.initCowritersSelection();
                this.initStartNotesButton();
                this.initParticipateNotesButton();
                this.initFindBuddiesButton();
                this.initSeeProfileLink();
                this.initHubLink();
            });

            this.pushAnalytics = function(eventName) {
                window._gaq.push(['_trackEvent', 'Buddies', 'results', eventName]);
            }

            this.initActivityFeed = function () {
                this.select('activityFeed').activityFeed(
                    {
                        documents: {
                            enabled: true,
                            itemTemplate: $('#activity_feed_item_template').html()
                        },
                        userId: this.attr.fromHub,
                        withPagination: true,
                        maxItems: 12
                    });
            }

            this.initCowritersSelection = function () {
                var $userProfiles = this.select('usersProfiles'), $iconsAddRemove = this.select('removeCowriterButton');

                if($userProfiles.length) {
                    this.attr.cowritersSelected = $userProfiles.map(function () { return $(this).attr('id'); }).get()
                }

                $userProfiles.find('.userphoto').click($.proxy(this.selectCowriters, this));
                $iconsAddRemove.click($.proxy(this.selectCowriters, this));
            }

            this.selectCowriters = function (event) {
                var $target = $(event.target),
                    $userProfile = $target.closest('.user'),
                    $iconAddRemove = $userProfile.find('.icon-remove,.icon-plus-sign'),
                    $userPhoto = $userProfile.find('.userphoto'),
                    user_id=$userProfile.attr('id'),
                    idx = this.attr.cowritersSelected.indexOf(user_id);

                if($userPhoto && $userPhoto.hasClass('background_active')) {
                    $userPhoto.removeClass('background_active');
                    $iconAddRemove.removeClass('icon-remove').addClass('icon-plus-sign');
                    if(idx!=-1) this.attr.cowritersSelected.splice(idx, 1);
                    this.pushAnalytics('remove cowriter');
                }
                else {
                    $userPhoto.addClass('background_active');
                    $iconAddRemove.removeClass('icon-plus-sign').addClass('icon-remove');
                    if(idx===-1) this.attr.cowritersSelected.push(user_id);
                    this.pushAnalytics('add cowriter');
                }
            }

            this.initStartNotesButton = function () {
                this.select('startNotesButton').click($.proxy(this.startNotes, this));
            }

            this.startNotes = function () {
                this.pushAnalytics("start notes with them");

                if(this.attr.cowritersSelected.length) {
                    var $startNotesButton = this.select('startNotesButton'), baseUrl = $startNotesButton.attr('href');
                    window.open(baseUrl + '&cowriters=' + encodeURIComponent(this.attr.cowritersSelected.join(',')));
                    return false;
                }

                return true;
            }

            this.initParticipateNotesButton = function () {
                this.select('findBuddiesButton').click($.proxy(this.pushAnalytics, this, "participate notes"));
            }

            this.initFindBuddiesButton = function () {
                this.select('findBuddiesButton').click($.proxy(this.findBuddies, this));
            }

            this.findBuddies = function (event) {
                var id = $(event.target).attr('id');
                this.pushAnalytics(id);
            }

            this.initSeeProfileLink = function () {
                this.select('profileLink').click($.proxy(this.pushAnalytics, this, "see cowriter's profile"));
            }

            this.initHubLink = function () {
                this.select('hubLink').click($.proxy(this.pushAnalytics, this, "hub link"));
            }
        }
    });

require(['noteTakingBuddyResults'],
function (NoteTakingBuddyResults) {
    $(document).ready(NoteTakingBuddyResults.attachTo($('.leadboard'), {
        fromHub: $('#fromHub').val()
    }));
})