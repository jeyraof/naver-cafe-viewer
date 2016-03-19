# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, jsonify
from flask.ext.sqlalchemy import SQLAlchemy
from requests import get
from lxml import html
from settings import FLASK_APP_CONFIG

from datetime import datetime, timedelta
import re

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


@app.route('/api/comments/')
def get_comments():
    args = request.args
    club_id = args.get('club_id')
    article_id = args.get('article_id')

    article_url = 'http://m.cafe.naver.com/ArticleRead.nhn?clubid=%s&articleid=%s' % (club_id, article_id)
    response = get(url=article_url, headers={'Referer': 'http://search.naver.com'})
    html_string = response.text
    dom = html.fromstring(html_string)

    sel_comment = dom.cssselect('a.cmt_num')
    if not sel_comment:
        return None

    comment_link = sel_comment[0].get('class', '')
    comment_info_re = re.search(r'\((.*)\)', comment_link)
    comment_info = str(comment_info_re.group(1)).split('|')

    comment_sc = comment_info[-1].split('=')[-1]

    comment_url = 'http://m.cafe.naver.com/CommentView.nhn?search.clubid=%s&search.articleid=%s&sc=%s' % (club_id,
                                                                                                          article_id,
                                                                                                          comment_sc)

    response = get(url=comment_url, headers={'Referer': 'http://search.naver.com'})
    html_string = response.text
    dom = html.fromstring(html_string)

    comment_list = dom.cssselect('ul.cmt_lst li')
    result_comment = []
    for comment in comment_list:
        temp_comment = {
            'class': comment.get('class', ''),
            'author': comment.cssselect('strong > a')[0].text_content().strip(),
            'content': comment.cssselect('div.clst_cont > span')[0].text_content().strip(),
        }
        result_comment.append(temp_comment)

    return render_template('commentList.html', comment_list=result_comment)


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

        if 'http://' not in url:
            url = 'http://' + url

        if 'cafe.naver.com' not in url:
            return None

        if 'm.cafe.naver.com' not in url:
            url = url.replace('cafe.naver.com', 'm.cafe.naver.com')

        response = get(url=url, headers={'Referer': 'http://m.search.naver.com/search.nhn?query=1'})
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
        for sel_thumb in sel_thumbnail:
            img_url = sel_thumb.get('src', '')
            if 'mcafethumb' in img_url:
                thumbnail = img_url
                break

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
    return txt.replace('\\r', '').replace('\\n', '').replace('\\t', '')
