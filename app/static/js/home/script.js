function _resizeFunction() {
    const start = 320;
    const range = 448;
    const width = window.innerWidth;
    const elem = document.getElementById("scene");
    if (width > start && width < (start + range)) {
        const p = (width - start) / range;
        elem.style.zoom = 1 + p * 0.5;
        elem.style.top = p * -37 + 'px';
    } else {
        elem.style.zoom = 0;
        elem.style.top = 0;
    }
}
function _roll(parent, totalTime = 50000) {
    if (typeof _rollParentWidth === 'undefined') {
        _rollParentWidth = parent.width();
    }
    var first = parent.find('li:eq(0)');
    var second = parent.find('li:eq(1)');
    var offset = second.offset();
    var left = Math.abs(parseInt(offset.left));
    var marginLeft = parseInt(first.css('marginLeft'));
    var time = parseInt(totalTime * (offset.left / parent.width()));
    first.animate({'marginLeft': -left+marginLeft}, time, 'linear', function () {
        parent.append(first);
        first.css('marginLeft', '');
        _roll(parent, totalTime);
    });
}
function _initFunction() {
    _resizeFunction();
    var scene = document.getElementById('scene');
    new Parallax(scene);

    var parent = $('.page-home .block-d ul');
    _roll(parent);
    parent.on("mouseleave", function () {
        _roll(parent);
    });
}

window.addEventListener('load', _initFunction, false);
window.addEventListener('resize', _resizeFunction, false);
