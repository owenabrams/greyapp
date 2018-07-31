var offsets = [];
var toggle = true;
function destak(elem) {
    elem.on('mouseover', function () {
        var w = $(this).width();
        var h = $(this).height();
        $(this).siblings().stop().fadeTo(300, 0.4);
        $(this).css({
            'maxWidth': w,
            'maxHeight': h
        });
        $(this).find('img').css('zoom', '105%');
    }).on("mouseleave", function () {
        $(this).siblings().stop().fadeTo(300, 1.0);
        $(this).css({
            'maxWidth': '',
            'maxHeight': ''
        });
        $(this).find('img').css('zoom', '');
    });
}
function mapBlockOffsets() {
    offsets = [];
    offsets[0] = 'white';
    $('[navbar-theme]').each(function () {
        offsets[Math.floor($(this).offset().top)] = $(this).attr('navbar-theme');
    });
    var last = offsets[0];
    for (i = 0; i <= $('body').height(); i++) {
        if (typeof offsets[i] === 'undefined') {
            offsets[i] = last;
        } else {
            last = offsets[i];
        }
    }
    scrollFunction();
}
function isMobile() {
    return window.innerWidth < 768;
}
function opacityFunction(elem) {
    const start = 20;
    const range = 200;
    const offset = window.pageYOffset;
    if (offset <= start) {
        elem.style.opacity = 1;
        elem.style.visibility = "visible";
    } else if (offset < start + range) {
        elem.style.opacity = 1 - ((offset - start) / range);
        elem.style.visibility = "visible";
    } else {
        elem.style.opacity = 0;
        elem.style.visibility = "hidden";
    }
}
function scrollFunction() {
    var range = 30;
    if (isMobile()) {
        if (!toggle) {
            var elem = document.getElementById("menu");
            elem.style.opacity = 1;
            elem.style.visibility = "visible";
            toggle = true;
        }
        $('#app').removeClass().addClass(offsets[window.pageYOffset + range]);
        var o = document.getElementById("top-brand");
        if (o) {
            opacityFunction(o);
        }
    } else {
        var elem = document.getElementById("top-brand");
        if (toggle && elem) {
            elem.style.opacity = 1;
            elem.style.visibility = "visible";
            toggle = false;
        }
        $('#app').removeClass().addClass(offsets[range]);
        opacityFunction(document.getElementById("menu"));
    }
}
function resizeFunction() {
    mapBlockOffsets();
    loadImagesFunction();
}
function loadImagesFunction() {
    let varstyle_mobile = '', varstyle = '<style>\n';
    $('[bg-img]').each(function (i) {
        const elem = $(this);
        let src, id, size, options;
        id = 'loadedImage' + i;
        elem.attr('id', id);
        varstyle += '#' + id + ' {';
        if (elem[0].hasAttribute('bg-img-m')) {
            varstyle_mobile += '#' + id + " {background-image: url('" + elem.attr('bg-img-m') + "');}\n";
        }
        if (elem[0].hasAttribute('bg-img')) {
            varstyle += "background-image: url('" + elem.attr('bg-img') + "');";
        }
        if (elem[0].hasAttribute('bg-img-size')) {
            size = elem.attr('bg-img-size');
        } else {
            size = 'auto 100%';
        }
        varstyle += " background-size: " + size + ";";
        varstyle += " background-repeat: no-repeat;";
        src = isMobile() ? elem.attr('bg-img-m') : elem.attr('bg-img');
        $('<img/>').attr('src', src).on('load', function () {
            $(this).remove(); // prevent memory leaks
            elem.removeAttr('bg-img bg-img-m bg-img-size');
        });
        varstyle += '}\n';
    });
    if (varstyle_mobile !== '') {
        varstyle += "@media (max-width: 767px) {\n" + varstyle_mobile + "}\n";
    }
    $(varstyle + '</style>').appendTo('head');
}
function _form(formId, error) {
    if(!$(formId).length) {
        return false;
    }
    $(formId).submit(function (e) {
        e.preventDefault();
        var inputs = $(formId).validator({
            lang: $('html').attr('lang'),
            position: 'bottom left',
            messageClass: error
        });
        if (!inputs.data("validator").checkValidity()) {
            return false;
        }
        var actionurl = e.currentTarget.action;
        var elem = $(this);
        var success = elem.attr('success');
        var fail = elem.attr('fail');
        var data = $(formId).serialize();
        $.ajax({
            url: actionurl,
            type: 'post',
            data: data,
            success: function (result) {
                if (result) {
                    alert(success);
                    elem.trigger("reset");
                } else {
                    alert(fail);
                }
            }
        });
    });
}
function newsletter() {
    _form("#app-newsletter", "error-newsletter");
}
function hashtag() {
    _form("#app-hashtag", "error-hashtag");
}
function initFunction() {
    resizeFunction();
    destak($('li.destak'));
    var cl = cloudinary.Cloudinary.new({cloud_name: "ddabodatx"});
    cl.responsive();
    $(".collapse").on('show.bs.collapse', function () {
        $("#menu").css('z-index', 9999);
    });
    $(".collapse").on('hide.bs.collapse', function () {
        $("#menu").css('z-index', '1000');
    });
    newsletter();
    hashtag();
}

loadImagesFunction();
window.addEventListener('load', initFunction, false);
window.addEventListener('scroll', scrollFunction, false);
window.addEventListener('resize', resizeFunction, false);

$.tools.validator.fn("[minlength]", {'en': 'Please enter a value that is at least $1 characters', 'pt': 'Mínimo de $1 caracteres', 'es': 'Mínimo de $1 caracteres'}, function (input) {
    var pass, minlength = input.attr("minlength"), length = $(input).val().length;
    if (length < minlength) {
        $(input).addClass("invalid");
        pass = [minlength];
    } else {
        $(input).removeClass("invalid");
        pass = true;
    }
    return pass;
});

$.tools.validator.fn("[unique]", {'en': 'Email already exists', 'pt': 'E-mail já cadastrado', 'es': 'Email ya existe'}, function (input) {
    var pass = false;
    var form = input.parents('form');
    $.ajax({
        url: form.attr('action') + '/unique/' + input.val(),
        type: 'get',
        async: false,
        success: function (result) {
            if (result) {
                $(input).removeClass("invalid");
                pass = true;
            } else {
                $(input).addClass("invalid");
            }
        }
    });
    return pass;
});

$.tools.validator.localize("pt", {
    ':email': 'Informe um email válido',
    '[required]': 'Campo obrigatório'
});

$.tools.validator.localize("es", {
    ':email': 'Introduzca un email válido',
    '[required]': 'Campo obligatorio'
});
