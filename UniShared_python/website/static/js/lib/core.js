define(function () {
    need_refresh = false;

    $(window).focus(function () {
        if (need_refresh) {
            need_refresh = false;

            $(window).trigger('refresh.unishared');
        }
    });

    $("[rel=tooltip]").tooltip();

    var uvOptions = {};
    (function () {
        var uv = document.createElement('script');
        uv.type = 'text/javascript';
        uv.async = true;
        uv.src = ('https:' == document.location.protocol ? 'https://' : 'http://') + 'widget.uservoice.com/' + userVoiceWidgetId + '.js';
        var s = document.getElementsByTagName('script')[0];
        s.parentNode.insertBefore(uv, s);
    })();

    Date.prototype.addHours = function (n) {
        this.setHours(this.getHours() + n);
    }
    Date.prototype.addMinutes = function (n) {
        this.setMinutes(this.getMinutes() + n);
    }

    //first, checks if it isn't implemented yet
    if (!String.prototype.format) {
        String.prototype.format = function() {
            var args = arguments;
            return this.replace(/{(\d+)}/g, function(match, number) {
                return typeof args[number] != 'undefined'
                    ? args[number]
                    : match
                    ;
            });
        };
    }

// Facebook SDK
    window.fbAsyncInit = function () {
        FB.init({
            appId: fb_appId,
            status: true, // check login status
            cookie: true, // enable cookies to allow the server to access the session
            xfbml: true // parse XFBML
        });

        FB.getLoginStatus(function (oResponse) {
            if (oResponse.status === 'connected') {
                // the session is complete, and fully initiated,
                // go ahead and call your scripts here
                fbApiInit = true; //init flag
            } else {
                // There was a problem, probably because the user was not logged in,
                // so put a login sequence or your error handling of choice here
            }
        });
    };

// Load the SDK Asynchronously
    ( function (d) {
        var js, id = 'facebook-jssdk', ref = d.getElementsByTagName('script')[0];
        if (d.getElementById(id)) {
            return;
        }
        js = d.createElement('script');
        js.id = id;
        js.async = true;
        js.src = "//connect.facebook.net/en_US/all.js";
        ref.parentNode.insertBefore(js, ref);
    }(document));

    window.fbEnsureInit = function (callback) {
        if (!window.fbApiInit) {
            setTimeout(function () {
                fbEnsureInit(callback);
            }, 50);
        } else {
            if (callback) {
                callback();
            }
        }
    }

// Google Analytics
    window._gaq = window._gaq || [];
    window._gaq.push(['_setAccount', ga_trackId]);
    window._gaq.push(['_setDomainName', domain]);
    window._gaq.push(['_trackPageview']);
    (function () {
        var ga = document.createElement('script');
        ga.type = 'text/javascript';
        ga.async = true;
        ga.src = ('https:' == document.location.protocol ? 'https://ssl' : 'http://www') + '.google-analytics.com/ga.js';
        var s = document.getElementsByTagName('script')[0];
        s.parentNode.insertBefore(ga, s);
    })();

    window.onerror = function (message, url, line) {
        if (typeof (window._gaq) === "object") {
            window._gaq.push(["_trackEvent", "JS Exception Error", message, (url + " (" + line + ")"), 0, true]);
        }
    };

    !function (d, s, id) {
        var js, fjs = d.getElementsByTagName(s)[0];
        if (!d.getElementById(id)) {
            js = d.createElement(s);
            js.id = id;
            js.src = "//platform.twitter.com/widgets.js";
            fjs.parentNode.insertBefore(js, fjs);
        }
    }(document, "script", "twitter-wjs");

// Google + 1 button
    (function () {
        var po = document.createElement('script');
        po.type = 'text/javascript';
        po.async = true;
        po.src = 'https://apis.google.com/js/plusone.js';
        var s = document.getElementsByTagName('script')[0];
        s.parentNode.insertBefore(po, s);
    })();

    /*
     Redefine Bootstrap tooltip show function.
     Conflict between the original behaviour which add the tooltip after the element
     And jCarouselLite which needs 'position:relative' to run the cursor.
     */
    $.fn.tooltip.Constructor.prototype.show =
        function () {
            var $tip
                , inside
                , pos
                , actualWidth
                , actualHeight
                , placement
                , tp

            if (this.hasContent() && this.enabled) {
                $tip = this.tip()
                this.setContent()

                if (this.options.animation) {
                    $tip.addClass('fade')
                }

                placement = typeof this.options.placement == 'function' ?
                    this.options.placement.call(this, $tip[0], this.$element[0]) :
                    this.options.placement

                inside = /in/.test(placement)

                $tip
                    .detach()
                    .css({ top: 0, left: 0, display: 'block' })
                    .appendTo('body');

                pos = this.getPosition(inside)

                actualWidth = $tip[0].offsetWidth
                actualHeight = $tip[0].offsetHeight

                switch (inside ? placement.split(' ')[1] : placement) {
                    case 'bottom':
                        tp = {top: pos.top + pos.height, left: pos.left + pos.width / 2 - actualWidth / 2}
                        break
                    case 'top':
                        tp = {top: pos.top - actualHeight, left: pos.left + pos.width / 2 - actualWidth / 2}
                        break
                    case 'left':
                        tp = {top: pos.top + pos.height / 2 - actualHeight / 2, left: pos.left - actualWidth}
                        break
                    case 'right':
                        tp = {top: pos.top + pos.height / 2 - actualHeight / 2, left: pos.left + pos.width}
                        break
                }

                $tip
                    .offset(tp)
                    .addClass(placement)
                    .addClass('in')
            }
        };

    window.ajaxSend = function (url, method, data, success_handler, error_handler) {
        $.ajax({
            url: url,
            type: method,
            dataType: 'json',
            data: data,
            success: success_handler,
            error: error_handler,
            beforeSend: function (xhr, settings) {
                function getCookie(name) {
                    var cookieValue = null;
                    if (document.cookie && document.cookie != '') {
                        var cookies = document.cookie.split(';');
                        for (var i = 0; i < cookies.length; i++) {
                            var cookie = jQuery.trim(cookies[i]);
                            // Does this cookie string begin with the name we want?
                            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                                break;
                            }
                        }
                    }
                    return cookieValue;
                }

                if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
                    // Only send the token to relative URLs i.e. locally.
                    xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
                }
            }
        });
    }

    window.getUrlVars = function () {
        var vars = [], hash;
        var hashes = window.location.href.slice(window.location.href.indexOf('?') + 1).split('&');

        for (var i = 0; i < hashes.length; i++) {
            hash = hashes[i].split('=');
            vars.push(hash[0]);
            vars[hash[0]] = hash[1];
        }

        return vars;
    }
});