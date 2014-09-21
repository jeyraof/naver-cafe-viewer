/**
 * Created by Jaeyoung on 9/21/14.
 */

$(document).ready(function() {
  var $body = $('body');

  // http://thecodeplayer.com/walkthrough/ripple-click-effect-google-material-design
  $body.on('click', 'a.article-link', function(e) {
    var parent = $(this).parent();
    if (parent.find(".ink").length == 0) parent.prepend("<span class='ink'></span>");
    var ink = parent.find(".ink");
    ink.removeClass("animate");
    if (!ink.height() && !ink.width()) {
      var d = Math.max(parent.outerWidth(), parent.outerHeight());
      ink.css({height: d, width: d});
    }
    var x = e.pageX - parent.offset().left - ink.width() / 2;
    var y = e.pageY - parent.offset().top - ink.height() / 2;
    ink.css({top: y + 'px', left: x + 'px'}).addClass("animate");
  });
});