/**
 * Created by Jaeyoung on 9/21/14.
 */

$(document).ready(function() {
  $(window).on('hashchange', ncvRoute);

  var $body = $('body');

  $body.on('click', '.header .title', function(e) {
    location.href = $(this).data('root');
  });

  $body.on('click', 'a.article-link', function(e) {
    // http://thecodeplayer.com/walkthrough/ripple-click-effect-google-material-design
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

  $body.on('submit', 'form#new-article', function() {
    var form = document.getElementById('new-article');
    $.ajax({
      type: 'POST',
      url: form.action,
      cache: false,
      async: false,
      data: $(form).serialize(),
      dataType: 'json',
      success: function(data) {
        if (data.ok) {
          window.location.hash = '#article@' + data.article_id;
        } else{
          alert(data.msg);
        }
      }
    });
    $(form).val('');
    return false;
  });

  $body.on('click', '.comment-load-btn', function() {
    $.ajax({
      url: this.href,
      dataType: 'html',
      success: function(data) {
        if (data === '') {
          alert('댓글이 없습니다.');
        } else {
          $('.comment-list').html(data);
        }
      }
    });
    return false;
  });
});

function ncvRoute() {
  var source = window.location.hash ? window.location.hash.substring(1) : '';
  var routeMap = {
    'article': getArticle
  };
  var html = '';
  if (source.indexOf('@') > -1) {
    var sourceMap = source.split('@');
    var contentType = sourceMap[0];
    var contentId = sourceMap[1];
    html = routeMap[contentType](contentId);
  } else {
    html = 'No contents';
  }

  drawContent(html);
}

function drawContent(html) {
  debug = html;
  $('.content-box').html(html);
}

function getArticle(id) {
  var url = '/api/article/' + id;
  var result = '';
  $.ajax({
    type: 'GET',
    url: url,
    cache: false,
    async: false,
    dataType: 'html',
    success: function(data) {
      result = data;
    }
  });
  return result;
}