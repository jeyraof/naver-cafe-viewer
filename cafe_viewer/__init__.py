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
def material():
    opt = {
        'article_list': Article.query.order_by('-last_view')[:10]
    }
    return render_template('material.html', **opt)


@app.route('/api/article/<int:article_id>')
def get_article(article_id):
    article = Article.get_by(article_id)
    opt = {
        'article': article,
    }

    return render_template('article.html', **opt)


@app.route('/api/article/new', methods=['POST'])
def new_article():
    url = request.form.get('link')
    article = Article.crawl(url)

    if article:
        opt = {'ok': True, 'article_id': article.id}
    else:
        opt = {'ok': False, 'msg': u'알아올 수 없는 포스트 입니다.'}
    return jsonify(**opt)


class Article(db.Model):
    __tablename__ = 'articles'
    id = db.Column(db.Integer, primary_key=1)
    club_id = db.Column(db.Integer, index=1, nullable=0)
    article_id = db.Column(db.Integer, index=1, nullable=0)
    title = db.Column(db.String(255), nullable=0)
    content = db.Column(db.Text)
    thumbnail = db.Column(db.String(255), nullable=1)
    author = db.Column(db.String(50))
    hit = db.Column(db.Integer, default=1)
    last_view = db.Column(db.DateTime, nullable=0)

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
        db.session.commit()
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
            print 1
            return None
        club_id = sel_club_id[0].get('value')

        sel_article_id = dom.cssselect('form[name="articleDeleteFrm"] input[name="articleid"]')
        if not sel_article_id:
            print 2
            return None
        article_id = sel_article_id[0].get('value')

        # check database
        article = cls.query.filter(cls.club_id == club_id, cls.article_id == article_id).first()
        if article:
            print 3
            return article

        # title
        sel_title = dom.cssselect('div.post_tit h2')
        if not sel_title:
            print 4
            return None
        title = sel_title[0].text_content().strip()

        # author
        sel_author = dom.cssselect('a.nick')
        if not sel_author:
            print 5
            return None
        author = sel_author[0].text_content().strip()

        # content
        sel_content = dom.cssselect('div#postContent')
        if not sel_content:
            print 6
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


@app.template_filter()
def ignore_nl(txt):
    result = txt.replace('\\r', '').replace('\\n', '').replace('\\t', '')
    return result