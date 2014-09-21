/**
 * Created by Jaeyoung on 9/21/14.
 */

$(document).ready(function() {
  var $body = $('body');

  // http://thecodeplayer.com/walkthrough/ripple-click-effect-google-material-design
  $body.on('click', 'a.article-link', function(e) {
    var parent = $(this).parent();
    if (parent.find(".material-ink").length == 0) parent.prepend("<span class='material-ink'></span>");
    var materialInk = parent.find(".material-ink");
    materialInk.removeClass("animate");
    if (!materialInk.height() && !materialInk.width()) {
      var d = Math.max(parent.outerWidth(), parent.outerHeight());
      materialInk.css({height: d, width: d});
    }
    var x = e.pageX - parent.offset().left - materialInk.width() / 2;
    var y = e.pageY - parent.offset().top - materialInk.height() / 2;
    materialInk.css({top: y + 'px', left: x + 'px'}).addClass("animate");
  });
});