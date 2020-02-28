// Triggered on post moderation.
function moderate_post(elem) {
    var post_id = elem.attr('data-value')
    var modpanel = $('#modpanel')
    if (modpanel.length > 0) {
        $('#modpanel').remove()
    } else {
        var page = $('<div id="modpanel"></div>').load("/local/moderate/post/" + post_id + "/")
        elem.parent().parent().after(page)
    }
}

// Triggered on user moderation.
function moderate_user(elem) {
    var user_id = elem.attr('data-value')
    var modpanel = $('#modpanel')
    if (modpanel.length > 0) {
        $('#modpanel').remove()
    } else {
        // Passing a data forces a POST request.
        var page = $('<div id="modpanel"></div>').load("/local/moderate/user/" + user_id + "/")
        // Insert the result
        elem.parent().parent().after(page)
    }
}

// Comments by authenticated users.
function add_comment(elem) {

    // remove comment body if exists.
    $("#comment-row").remove();

    var post_id = elem.attr('data-value')
    var container = elem.parent().parent()

    // TODO: remove java script
    container.after('<div id="comment-row">\
    <form id="comment-form" role="form" action="/x/new/comment/' + post_id + '/" method="post"> \
        <div class="form-group">\
        <div class="wmd-panel">\
            <div id="wmd-button-bar-2"></div>\
            <textarea class="wmd-input-2" id="wmd-input-2"  name="content" rows="3"></textarea></div> \
        </div>\
        <div><a class="btn btn-success" href=\'javascript:document.forms["comment-form"].submit()\'><i class="icon-comment"></i> Add comment</a>          \
        <a class="btn btn-warning pull-right" onclick="javascript:obj=$(\'#comment-row\').remove();"><i class="icon-remove"></i> Cancel</a>   </div>       \
    </form>            \
    </div>'
    )

    var converter = new Markdown.Converter();
    var editor = new Markdown.Editor(converter, '-2');
    editor.run();

}

// modifies the votecount value
function mod_votecount(elem, k) {
    count = parseInt(elem.siblings('.count').text()) || 0
    count += k
    elem.siblings('.count').text(count)
}


VOTE = "vote"

function toggle_button(elem, vote_type) {
    // Toggles the state of the buttons and updates the label messages
    if (elem.hasClass('off')) {
        elem.removeClass('off');
        change = 1
    } else {
        elem.addClass('off');
        change = -1
    }
    mod_votecount(elem, change)
}

function pop_over(elem, msg, cls) {
    var text = '<div></div>'
    var tag = $(text).insertAfter(elem)
    tag.addClass('vote-popover alert ' + cls)
    tag.text(msg)
    tag.delay(1000).fadeOut(1000, function () {
        $(this).remove()
    });
}


function title_format(row) {
    link = '<a href="' + row.url + '"/>' + row.text + '</a><div class="in">' + row.context + ' by <i>' + row.author + '</i></div>';
    return link
}

$(document).ready(function () {
    var tooltip_options = {};


    var wmd = $('#wmd-input')
    if (wmd.length) {
        var converter = new Markdown.Converter();
        var editor = new Markdown.Editor(converter);
        editor.run();
    }


    var searchform = $("#searchform")

    if (searchform.length > 0) {
        searchform.focus();

        // Add the search functionality
        searchform.select2({
            placeholder: "Live search: start typing...",
            minimumInputLength: 3,
            ajax: {
                url: TITLE_SEARCH_URL,
                dataType: 'json',
                data: function (term, page) {
                    return {
                        q: term, // search term
                        page_limit: 10
                    };
                },
                results: function (data, page) {
                    console.log(data.items)
                    console.log(page)
                    return {results: data.items};
                }
            },

            formatResult: title_format,

            dropdownCssClass: "bigdrop",
            escapeMarkup: function (m) {
                return m;
            }
        })
        searchform.on("change", function (e) {
            window.location = e.val
        })
    }


    // This gets triggered only if tag recommendation
    // becomes necessary.
    var tagval = $("#id_tag_val")

    if (tagval.length > 0) {
        tagval.removeClass("textinput textInput form-control")
        tagval.width("96%")

        var tag_list = $.ajax({
            url: "/local/search/tags/",
            dataType: 'json',
            success: function (response) {
                tagval.select2({
                    tags: response
                });
            }
        });
    }

    // Register tooltips.
    $('.tip').tooltip(tooltip_options)

    // Authenticated user actions.
    $('.add-comment').each(function () {
        $(this).click(function () {
            add_comment($(this));
        });
    });

    // Moderator actions.
    $('.mod-post').each(function () {
        $(this).click(function () {
            moderate_post($(this));
        });
    });

    // Moderator actions.
    $('.mod-user').each(function () {
        $(this).click(function () {
            moderate_user($(this));
        });
    });

})
;
