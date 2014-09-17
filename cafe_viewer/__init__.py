# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, jsonify, send_from_directory
from requests import get
from lxml import html


app = Flask(__name__)


@app.route('/')
def index():
    url = request.args.get('url', None)
    return render_template('index.html',
                           url=url)


@app.route('/parse', methods=['POST'])
def parse():
    url = request.form.get('url')
    if not url:
        jsonify(ok=False, msg=u'Not valid url')

    if not 'http://' in url:
        url = 'http://' + url

    if not 'm.cafe.naver.com' in url:
        url = url.replace('cafe.naver.com', 'm.cafe.naver.com')

    response = get(url=url, headers={'Referer': 'http://search.naver.com'})
    html_string = response.text
    dom = html.fromstring(html_string)

    # title
    sel_title = dom.cssselect('div.post_tit h2')
    if sel_title:
        title = sel_title[0].text_content().strip()
    else:
        return jsonify(ok=False, msg=u'could not find title')

    # author
    sel_author = dom.cssselect('a.nick')
    if sel_author:
        author = sel_author[0].text_content().strip()
    else:
        return jsonify(ok=False, msg=u'could not find author')

    # content
    sel_content = dom.cssselect('div#postContent')
    if sel_content:
        content = html.tostring(sel_content[0]).strip()
    else:
        return jsonify(ok=False, msg=u'could not find content')

    # meta
    sel_club_id = dom.cssselect('form[name="articleDeleteFrm"] input[name="clubid"]')
    if sel_club_id:
        club_id = sel_club_id[0].get('value')
    else:
        return jsonify(ok=False, msg=u'could not find club_id')

    sel_article_id = dom.cssselect('form[name="articleDeleteFrm"] input[name="articleid"]')
    if sel_article_id:
        article_id = sel_article_id[0].get('value')
    else:
        return jsonify(ok=False, msg=u'could not find article_id')

    return jsonify(ok=True,
                   url=url,
                   article={
                       'title': title,
                       'author': author,
                       'content': content,
                       'club_id': club_id,
                       'article_id': article_id,
                   })
