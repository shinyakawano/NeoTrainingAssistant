// variables
var coords = new Array();
var curr_crd;
var canvas;
var context;
var ratio;

var limit_upper_width;
var limit_upper_height;
var limit_lower_width;
var limit_lower_height;

var alert_click_clear;
var alert_click_skip;
var alert_click_next;


// onload
onload = function() {
    draw(redraw=0);

    $('#undo').on('click', function(){
        coords.pop();
        draw(redraw=1);
    });
    $('#clear').on('click', function(){
        if (alert_click_clear) {
            bootbox.confirm(
                "Clear all rectangles. Are you OK?",
                function(result) {
                    coords = new Array();
                    draw(redraw=0);
                });
        } else {
            coords = new Array();
            draw(redraw=0);
        }
    });

    $('#skip').on('click', function(){
        if (coords.length == 0) {
            next_ajax(skip=1);
        } else {
            if (alert_click_skip) {
                bootbox.alert("To use 'skip', please 'clear' all rectanges.");
            }
        }
    });
    $('#next').on('click', function(){
        if (coords.length > 0) {
            next_ajax(skip=0);
        } else {
            if (alert_click_next) {
                bootbox.alert("There is nothing to crop, please click 'skip'.");
            }
        }
    });
    $('#back').on('click', function(){
        back_ajax();
    });

    $('.bar').css({'width': count*100/imgnum + '%'});
};


// functions
function draw(redraw) {
    var image = new Image();
    image.src = imgsrc;

    image.onload = function(){
        var tmp_width  = this.width;
        var tmp_height = this.height;

        // extend
        if (tmp_width < limit_lower_width) {
            tmp_height *= (limit_lower_width / tmp_width)
            tmp_width   = limit_lower_width
        }
        if (tmp_height < limit_lower_height) {
            tmp_width  *= (limit_lower_height / tmp_height);
            tmp_height  = limit_lower_height
        }

        // shrink
        if (tmp_width > limit_upper_width) {
            tmp_height *= (limit_upper_width / tmp_width);
            tmp_width   = limit_upper_width;
        }
        if (tmp_height > limit_upper_height) {
            tmp_width  *= (limit_upper_height / tmp_height);
            tmp_height  = limit_upper_height;
        }

        ratio = tmp_width / this.width;

        var width  = tmp_width;
        var height = tmp_height;
        $('.main-wrapper').css({
            'width': width,
            'minWidth': width
        });

        var wrapper = $('#canvas-wrapper');
        $(wrapper).empty();
        var c = $('<canvas/>').attr('id', 'cnvs');
        $(wrapper).append(c);

        canvas = $('#cnvs').get(0);
        context = canvas.getContext('2d');
        $('#cnvs').css({
            'width' : width  + 'px',
            'height': height + 'px'
        }).attr({
            'width' : width  + 'px',
            'height': height + 'px'
        });
        context.drawImage(this, 0, 0, this.width, this.height, 0, 0, width, height);

        if (redraw == 1) {
            for (var i=0; i<coords.length; i++) {
                var curr_crd = coords[i];
                context.beginPath();
                context.lineWidth = 3;
                context.strokeStyle = 'rgba(238, 26, 26, 1)';
                context.strokeRect(curr_crd[0], curr_crd[1],
                        curr_crd[2], curr_crd[3]);
            }
        }

        $(function(){
            $('#cnvs').Jcrop({
                onSelect: selected,
                onRelease: released,
            });
        });

    }
}

function selected(c) {
    curr_crd = [c.x, c.y, c.w, c.h, ratio];
}

function released(c) {
    coords.push(curr_crd);

    context.beginPath();
    context.lineWidth = 3;
    context.strokeStyle = 'rgba(238, 26, 26, 1)';
    context.strokeRect(curr_crd[0], curr_crd[1],
            curr_crd[2], curr_crd[3]);
}

function next_ajax(skip) {
    coords = JSON.stringify(coords);

    $.ajax({
        type: "GET",
        dataType: "json",
        data: {"coords": coords, "skip": skip},
        url: "/_next",

        success: function (data) {
            imgsrc = data.imgsrc;
            coords = data.coords;

            console.log(coords);

            limit_upper_width  = data.size[0];
            limit_upper_height = data.size[1];
            limit_lower_width  = data.size[2];
            limit_lower_height = data.size[3];

            alert_click_clear = data.alert[0];
            alert_click_skip  = data.alert[1];
            alert_click_next  = data.alert[2];

            var count = data.count;
            var finished = data.finished;
            $('.bar').css({'width': count*100/imgnum + '%'});

            if (finished) {
                w = $('.head-wrapper').width()
                $('.main-wrapper').css({'width': w, 'minWidth': w});
                $('#canvas-wrapper').empty().append('<div class="message">'
                    + imgnum + ' images were <br />successfully processed!</div>');
                $('.btn').addClass('disabled');
                $('#clear').off('click');
            } else {
                var tmp = (count+1).toString();
                while(tmp.length < imgnum.toString.length){
                    tmp = '0' + tmp;
                }
                $('.count').html(tmp + ' of ' + imgnum);

            }

            draw(redraw=1);
        }

    });

}


function back_ajax() {
    $.ajax({
        type: "GET",
        dataType: "json",
        url: "/_back",

        success: function (data) {
            imgsrc = data.imgsrc;
            coords = new Array();
            coords = data.coords;

            limit_upper_width  = data.size[0];
            limit_upper_height = data.size[1];
            limit_lower_width  = data.size[2];
            limit_lower_height = data.size[3];

            alert_click_clear = data.alert[0];
            alert_click_skip  = data.alert[1];
            alert_click_next  = data.alert[2];

            var count = data.count;
            var finished = data.finished;
            $('.bar').css({'width': count*100/imgnum + '%'});

            var tmp = (count+1).toString();
            while(tmp.length < imgnum.toString.length){
                tmp = '0' + tmp;
            }
            $('.count').html(tmp + ' of ' + imgnum);

            draw(redraw=1);
        }

    });

}
