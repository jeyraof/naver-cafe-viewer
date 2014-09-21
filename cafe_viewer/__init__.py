# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, jsonify
from flask.ext.sqlalchemy import SQLAlchemy
from requests import get
from lxml import html
from settings import FLASK_APP_CONFIG

from datetime import datetime, timedelta

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

    return jsonify(ok=True,
                   url=url,
                   article={
                       'title': title,
                       'author': author,
                       'content': content,
                       'club_id': club_id,
                       'article_id': article_id,
                   })


@app.route('/material')
def material():
    opt = {
        'article_list': Article.query.order_by('-last_view')[:10]
    }
    return render_template('material.html', **opt)


class Article(db.Model):
    __tablename__ = 'articles'
    id = db.Column(db.Integer, primary_key=1)
    club_id = db.Column(db.Integer, index=1, nullable=0)
    article_id = db.Column(db.Integer, index=1, nullable=0)
    title = db.Column(db.String(255), nullable=0)
    content = db.Column(db.Text)
    thumbnail = db.Column(db.String(255), nullable=1)
    author = db.Column(db.String(50))
    hit = db.Column(db.Integer, default=0)
    last_view = db.Column(db.DateTime, nullable=0, default=0)

    __table_args__ = (db.UniqueConstraint('club_id', 'article_id', name='article_group'),)

    def __init__(self, **kwargs):
        self.last_view = datetime.utcnow()
        super(Article, self).__init__(**kwargs)

    @classmethod
    def get_by(cls, a_id):
        article = cls.query.filter(cls.id == a_id).first()

        if not article:
            return None

        article.hit += 1
        article.last_view = datetime.utcnow()
        return article

    @classmethod
    def crawl(cls, url=None):
        if not url:
            return None

        if not 'http://' in url:
            url = 'http://' + url

        if not 'm.cafe.naver.com' in url:
            url = url.replace('cafe.naver.com', 'm.cafe.naver.com')

        response = get(url=url, headers={'Referer': 'http://search.naver.com'})
        html_string = response.text
        dom = html.fromstring(html_string)

        # meta
        sel_club_id = dom.cssselect('form[name="articleDeleteFrm"] input[name="clubid"]')
        if not sel_club_id:
            return None
        club_id = sel_club_id[0].get('value')

        sel_article_id = dom.cssselect('form[name="articleDeleteFrm"] input[name="articleid"]')
        if not sel_article_id:
            return None
        article_id = sel_article_id[0].get('value')

        # check database
        article = cls.query.filter(cls.club_id == club_id, cls.article_id == article_id).first()
        if article:
            return article

        # title
        sel_title = dom.cssselect('div.post_tit h2')
        if not sel_title:
            return None
        title = sel_title[0].text_content().strip()

        # author
        sel_author = dom.cssselect('a.nick')
        if not sel_author:
            return None
        author = sel_author[0].text_content().strip()

        # content
        sel_content = dom.cssselect('div#postContent')
        if not sel_content:
            return None
        content = html.tostring(sel_content[0]).strip()

        # thumbnail
        sel_thumbnail = dom.cssselect('div#postContent img')
        thumbnail = None
        if sel_thumbnail:
            thumbnail = sel_thumbnail[0].get('src')

        article = cls(**{
            'club_id': club_id,
            'article_id': article_id,
            'title': title.encode('unicode_escape'),
            'content': content,
            'thumbnail': thumbnail,
            'author': author.encode('unicode_escape'),
        })

        db.session.add(article)
        db.session.commit()
        db.session.refresh(article)
        return article


@app.template_filter()
def pretty_date(value):
    if not isinstance(value, datetime):
        return value
    now = datetime.utcnow()
    if value > now:
        return value  # 이건 어떻게 처리해야 하는거야?
    delta = now - value
    if delta < timedelta(minutes=1):
        return u'%s초 전' % delta.seconds
    elif delta < timedelta(hours=1):
        return u'%s분 전' % (delta.seconds / 60)
    elif delta < timedelta(days=1):
        return u'%s시간 전' % (delta.seconds / 3600)
    elif now.year == value.year:
        return value.strftime(u'%m/%d')
    else:
        return value.strftime(u'%y/%m/%d')