# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, jsonify
from requests import get
from lxml import html


app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


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

    return jsonify(ok=True,
                   url=url,
                   article={
                       'title': title,
                       'author': author,
                       'content': content,
                   })