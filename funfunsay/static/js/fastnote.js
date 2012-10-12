!function ($) {
//(function($){

    //Attach this new method to jQuery
    loadMoreNotes = function (options) {
        //Set the default values, use comma to separate the settings, example:
        var defaults = {
            url: $SCRIPT_ROOT + '_fetch_notes',
            filterid: '',
            authorid: '',
            threadid: $(window).data('activethreadid'),
            paperid: $(window).data('activepaperid'),
            tags: "",
            sort: 'naturally',
            keywords: "",
            direction: "",
            criteria: "",
            number: 20,
            sharedonly: false,
            clear: false,
            lastIds: "",
            container: $('#noteList'),
            scroller: $(window),
            loader: $('div#lazyLoaderDiv'),
            tips: "Loading more notes...",
            nomoreTips: "No more notes.",
            loaderimg: "/static/bigLoader.gif",
            _onstart: function () {
                //alert('_onstart');
                defaults.loader.html('<h3><small>' + defaults.tips + '</small></h3><img src=' + defaults.loaderimg + '>');
                defaults.onstart();
            },
            _onfinish: function (data) {
                //alert('_onfinish');
                defaults.loader.empty();
                defaults.onfinish(data);
            },
            _onnomore: function () {
                defaults.loader.html('<h3><small>' + defaults.nomoreTips + '</small></h3>');
            },
            onstart: function () {

            },
            onfinish: function (data) {

            }
        };

        var options = $.extend(defaults, options);

        var o = options;

        if (o.clear) {
            //alert("clear");
            o.container.empty();
            o.container.data("nomore", false);
        }

        //alert(lastIds);
        if (o.container.data("nomore") == true) {
            //alert(' no need!');
            o._onnomore();
        }
        else {
            o._onstart();

            $.get(o.url, {
                authorid: o.authorid,
                lastIds: o.lastIds,
                number: o.number,
                threadid: o.threadid,
                paperid: o.paperid,
                tags: o.tags,
                clear: o.clear,
                sharedonly: o.sharedonly,
                sort: o.sort,
                direction: o.direction,
                criteria: o.criteria
            },
            function (data) {
                if (data.status == true) {
                    o.container.append(data.notes);
                } else {
                    if (data.noMore == true) {
                        o.container.data("nomore", true);
                    }
                }
                o._onfinish(data);
            });
        }
    } /*function load more notes*/

    //pass jQuery to the function,
    //So that we will able to use any valid Javascript variable name
    //to replace "$" SIGN. But, we'll stick to $ (I like dollar sign: ) )     
}(jQuery);
//})(jQuery);



