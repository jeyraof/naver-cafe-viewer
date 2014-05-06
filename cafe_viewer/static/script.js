$(document).ready(function() {
  var $form = $('form.url');

  $form.submit(function() {
    crawl_article($form);

    return false;
  });
});

function crawl_article($form) {
  $.post(
    $form.attr('action'),
    $form.serialize(),
    function (data) {
      if (data.ok) {
        $('h1.title').html(data.article.title);
        $('div.meta span.author').html('by. ' + data.article.author);
        $('div.body').html(data.article.content);
      } else {
        alert(data.msg || 'Error!');
      }
    }
  );
}