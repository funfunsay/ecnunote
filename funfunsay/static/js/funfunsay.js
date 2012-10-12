(function ($) {

    $.fn.modal_message_box = function (options) {
        var el = this;

        $("a.delete").hide();

        $("div.noteItem").hover(
            function () { $(this).find("a.delete").show(); },
            function () { $(this).find("a.delete").hide(); }
        );

        // transfer note id to modal 
        $("a.delete").on('click', function (e) {
            $('a#modalAction').attr("id", $(this).attr("id"));
            $('div#myModal div.modal-body p').html($(this).data("confirm"));
        });

        // perform modal "OK" action
        $('a#modalAction').on('click', function (e) {
            e.preventDefault();
            //delete note
            var noteid = $(this).attr("id").substring(8);
            $.post("{{url_for('funnote.delete_message')}}", {
                noteid: noteid
            }, function (data) {
                window.location.href = data.redirect;
            });
        });

    };

})(jQuery);
