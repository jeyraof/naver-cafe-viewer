# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, jsonify
from flask.ext.sqlalchemy import SQLAlchemy
from requests import get
from lxml import html
from settings import FLASK_APP_CONFIG

from datetime import datetime

app = Flask(__name__)
app.config.update(FLASK_APP_CONFIG)
db = SQLAlchemy(app)


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

    print club_id, article_id

    return jsonify(ok=True,
                   url=url,
                   article={
                       'title': title,
                       'author': author,
                       'content': content,
                       'club_id': club_id,
                       'article_id': article_id,
                   })


class Article(db.Model):
    __tablename__ = 'articles'
    id = db.Column(db.Integer, primary_key=1)
    club_id = db.Column(db.Integer, index=1, nullable=0)
    article_id = db.Column(db.Integer, index=1, nullable=0)
    content = db.Column(db.Text)
    author = db.Column(db.String(50))
    hit = db.Column(db.Integer, default=0)
    last_view = db.Column(db.DateTime, nullable=0, default=0)

    def __init__(self, **kwargs):
        self.last_view = datetime.utcnow()
        super(Article, self).__init__(**kwargs)

    def get_by(self, a_id):
        article = self.query.filter(self.id == a_id).first()

        if not article:
            return None

        article.hit += 1
        article.last_view = datetime.utcnow()
        return article