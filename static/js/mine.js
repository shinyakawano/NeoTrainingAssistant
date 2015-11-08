// variables
var coords = new Array();
var curr_crd;
var canvas;
var context;
var ratio;


// onload
onload = function() {
    draw(undo=0);

    $('#undo').click(function(){
        undo_status()
    });
    $('#clear').click(function(){
        if (confirm("Clear rectangles, OK?")) {
            clear_status();
        }
    });

    $('#skip').click(function(){
        next_ajax(skip=1);
    })
    $('#next').live('click', function(){
        next_ajax(skip=0);
    });

    $('.bar').css({'width': count*100/imgnum + '%'});
};


// functions
function draw(undo) {
    var image = new Image();
    image.src = imgsrc;
    image.onload = function(){
        var width  = image.naturalWidth;
        var height = image.naturalHeight;
        $('.main-wrapper').css({'width': width, 'minWidth': width});

        var wrapper = $('#canvas-wrapper');
        $(wrapper).empty();
        var c = $('<canvas/>').attr('id', 'cnvs');
        $(wrapper).append(c);

        canvas = $('#cnvs').get(0);
        context = canvas.getContext('2d');
        $('#cnvs').css({'width': width + 'px', 'height': height + 'px'}).attr(
                {'width': width + 'px', 'height': height + 'px'});
        context.drawImage(image, 0, 0);

        if (undo == 1) {
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
    curr_crd = [c.x, c.y, c.w, c.h];
}

function released(c) {
    coords.push(curr_crd);

    context.beginPath();
    context.lineWidth = 3;
    context.strokeStyle = 'rgba(238, 26, 26, 1)';
    context.strokeRect(curr_crd[0], curr_crd[1],
            curr_crd[2], curr_crd[3]);
}

function clear_status() {
    coords = new Array();
    draw(undo=0);
}

function undo_status() {
    coords.pop();
    draw(undo=1);
}

function next_ajax(skip) {
    console.log("coords : " + coords);
    coords = JSON.stringify(coords);

    $.ajax({
        type: "GET",
        dataType: "json",
        data: {"coords": coords, "skip": skip},
        url: "/_next",

        success: function (data) {
            imgsrc = data.imgsrc;
            var count = data.count;
            var finished = data.finished;
            $('.bar').css({'width': count*100/imgnum + '%'});
            console.log(count + '/' + imgnum);

            if (finished) {
                w = $('.head-wrapper').width()
                $('.main-wrapper').css({'width': w, 'minWidth': w});
                $('#canvas-wrapper').empty().append('<div class="message">'
                    + imgnum + ' images were successfully processed!</div>');
                $('.btn').addClass('disabled');
            } else {
                var tmp = (count+1).toString();
                while(tmp.length < imgnum.toString.length){
                    tmp = '0' + tmp;
                }
                $('.count').html(tmp + ' of ' + imgnum);
                clear_status();
            }
        }

    });

}

