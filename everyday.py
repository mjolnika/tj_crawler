import re
import urllib.request
import datetime
import html
import os
from urllib.error import HTTPError
import pandas as pd
import operator
from classes import *

#date from which to crawl
date = datetime.date.today() - datetime.timedelta(days=1)


#Ovozi
replace = ['© 2012-2018 "OvoziTojik.uz"   Все права защищены.']
re_links = re.compile('<h3><a href="(.*?)"', flags=re.DOTALL)
re_nextpage = re.compile('<li class="next"><a href="(.*?)"', flags=re.DOTALL)
re_title = re.compile('<h1>(.*?)</h1>', flags=re.DOTALL)
re_author = re.compile('<strong>.*?([А-ЯҶҒҚӮҲЭ][^ ]*? ?[А-ЯҶҒҚӮҲЭ]{3}[А-ЯҶҒҚӮҲЭ]*).*?</strong>', flags=re.DOTALL)
#<strong>К. САЛОМОВ,<br />\r\nомӯзгори фанни таърих.</strong>
re_date = re.compile('<i class="pe-7s-clock"></i> ?([0-9\-]*?) [0-9]', flags=re.DOTALL)
re_arttext = re.compile('<p>.*?</p>', flags=re.DOTALL)
url = 'http://ovozitojik.uz'
source = 'Ovozi Tojik'
#yesterday = datetime.date.today() - datetime.timedelta(days=1)
pre = []    
ovCrawl = OvoziCr(url, source, pre) 
re_sect = re.compile('class="last" title="[1-9]*?">', flags=re.DOTALL) 
ovCrawl.articles_from_date(date, re_nextpage=re_nextpage, re_date=re_date, re_sect=re_sect, re_links=re_links, re_arttext=re_arttext, re_title=re_title, re_author=re_author, replace=replace, op=operator.eq)
try:
    ovCrawl.articles_from_date(date, re_nextpage=re_nextpage, re_date=re_date, re_sect=re_sect, re_links=re_links, re_arttext=re_arttext, re_title=re_title, re_author=re_author, replace=replace, op=operator.eq)
except Exception as exc:
    print('Sorry, couldnt run download from ' + url + ' or 0 articles found, error: ')
    print(exc)


#Ossetin
replace = ["<div class=\"b-inject__copy\"><span>.*?</span></div>", "<p>[^/]*Sputnik\.","<figcaption.*?</figcaption>"]#©
re_arttext = re.compile('<p.*?>(.*?)</p>', flags=re.DOTALL)
re_title = re.compile('<title>(.*?)</title>', flags=re.DOTALL)
re_author = re.compile('<div class="b-article__header-copy"><span><span>.*?Sputnik.*?(\w.*?)</span></span>', flags=re.DOTALL)
url = 'https://sputnik-ossetia.com/'
source = 'Sputnik Хуссар Ирыстоны'
pre = ['<div class="b-banner m-banner-33 m-mb20 m-mt10">.*$', "</p>\r?\n?<blockquote class=\"marker-quote.\">", "<\blockquote>\r?\n?<p>"]
crawlOss = Crawler(url, source, pre) 
re_nav = re.compile('<ul class="b-mainnav__list">(.*?)</ul>', flags=re.DOTALL)
re_sect = re.compile('<li class="b-mainnav__item" data-list-id="[0-9]*?"><a href="/(\w*?/)">', flags=re.DOTALL)
dirs = crawlOss.extract_sections(re_sect, re_nav)
try:
    crawlOss.articles_from_date(date, dirs, re_arttext, re_title, re_author, replace)
except Exception as exc:
    print('Sorry, couldnt run download from ' + url + ' or 0 articles found, error: ')
    print(exc)



#Sputnik Taj
replace = ["<div class=\"b-inject__copy\"><span>.*?</span></div>", "<p>[^/]*Sputnik\.","<figcaption.*?</figcaption>"]
re_arttext = re.compile('<p.*?>(.*?)</p>', flags=re.DOTALL)
re_title = re.compile('<title>(.*?)</title>', flags=re.DOTALL)
re_author = re.compile('<div class="b-article__header-copy"><span><span>.*?Sputnik.*?(\w.*?)</span></span>', flags=re.DOTALL)
url = "https://sputnik-tj.com/"
source = 'Sputnik Таджикистан'
pre = ['<div class="b-banner m-banner-33 m-mb20 m-mt10">.*$', "</p>\r?\n?<blockquote class=\"marker-quote.\">", "<\blockquote>\r?\n?<p>"]
crawlSpTj = Crawler(url, source, pre) 
re_nav = re.compile('<ul class="b-mainnav__list">(.*?)</ul>', flags=re.DOTALL)
re_sect = re.compile('<li class="b-mainnav__item" data-list-id="[0-9]*?"><a href="/(\w*?/)">', flags=re.DOTALL)
dirs = crawlSpTj.extract_sections(re_sect, re_nav)
try:
    crawlSpTj.articles_from_date(date, dirs, re_arttext, re_title, re_author, replace)
except Exception as exc:
    print('Sorry, couldnt run download from ' + url + ' or 0 articles found, error: ')
    print(exc)


#Faraj
replace = []
re_links = re.compile('<div class="td-module-thumb"><a href=\"(.*?)\"', flags=re.DOTALL)
re_title = re.compile('<h1 class="entry-title">(.*?)</h1>', flags=re.DOTALL)
re_author = re.compile('<div class="td-post-author-name"><div class="td-author-by">Муаллиф</div> <a href=".*?">(.*?)</a>', flags=re.DOTALL)
re_arttext = re.compile('<div class="td-post-content tagdiv-type">.*?</div>', flags=re.DOTALL)
url = "https://faraj.tj/"
source = 'Фараж'
pre = []    
crawlFar = FarajCr(url, source, pre) 
re_sect = re.compile('class="last" title="[1-9]*?">', flags=re.DOTALL)
try: 
    crawlFar.articles_from_date(date, re_sect, re_links,  dirs, re_arttext, re_title, re_author, replace)
except Exception as exc:
    print('Sorry, couldnt run download from ' + url + ' or 0 articles found, error: ')
    print(exc)


#AsiaPlusTj
replace = []
re_links = re.compile('<div><a href=\"([^"]*?)\"><h3>', flags=re.DOTALL)
re_title = re.compile('<h1 class=\"atitle\"  >(.*?)</h1>', flags=re.DOTALL)
re_author = re.compile('<span class=\'article-author\'>(.*?)</span>', flags=re.DOTALL)
re_arttext = re.compile('<div class=\'article-body js-mediator-article\'>(.*?)<script class=', flags=re.DOTALL)
url = "https://asiaplustj.info/tj/news/all"
source = 'Asia-Plus'
pre = []    
crawlAsia = AsiaCr(url, source, pre)
dirs = []
re_sect = re.compile('<a href=\'/tj/news/all([?]page=[1-9]*?)\'', flags=re.DOTALL)
try: 
    crawlAsia.articles_from_date(date, re_sect, re_links,  dirs, re_arttext, re_title, re_author, replace)
except Exception as exc:
    print('Sorry, couldnt run download from ' + url + ' or 0 articles found, error: ')
    print(exc)


#Khovar
replace = []
re_links = re.compile('<a href=\"([^"]*?)\" class=\"more\">Матни пурра<span', flags=re.DOTALL)
re_title = re.compile('</div><h1>([^<]*?)</h1>', flags=re.DOTALL)
re_author = re.compile('<<p><strong>[^/]*?/([^/]*?)/.</strong><em>', flags=re.DOTALL)
re_arttext = re.compile('<p><strong>(.*?)<div class=\"ya-share2\" data-services=', flags=re.DOTALL)
#<a class='page-numbers' href='https://khovar.tj/lenta-novostey/page/3924/'>
re_sect = re.compile('<a class=\'page-numbers\' href=\'https://khovar.tj/lenta-novostey/page/([^/]*?)/\'>', flags=re.DOTALL)
url = "https://khovar.tj/"
source = 'Khovar'
pre = []    
crawlKhovar = KhovarCr(url, source, pre)
dirs = []

try: 
    crawlKhovar.articles_from_date(date, re_sect, dirs, re_links, re_arttext, re_title, re_author, replace)
except Exception as exc:
    print('Sorry, couldnt run download from ' + url + ' or 0 articles found, error: ')
    print(exc)

#OvoziSam
replace = []
re_links = re.compile('<h2 class=\"blog-entry-title entry-title\">[^<]*?<a href=\"([^"]*?)\"', flags=re.DOTALL)
re_title = re.compile('itemprop=\"headline\">([^<]*?)</h2>', flags=re.DOTALL)
re_author = re.compile('<p class=\"has-text-align-right\"><strong>([^<]*?)</strong>', flags=re.DOTALL)
re_arttext = re.compile('<div class=\"entry-content clr\" itemprop=\"text\">(.*?)<p class', flags=re.DOTALL)
#<a class='page-numbers' href='https://khovar.tj/lenta-novostey/page/3924/'>
re_sect = re.compile('class=\"pagination__number\">([^<]*?)</a>', flags=re.DOTALL)
url = "https://ovozisamarqand.uz/"
source = 'Ovozi Samarqand'
pre = []    
crawlOvoziSam = OvoziSamCr(url, source, pre)
dirs = []
try:
    crawlOvoziSam.articles_from_date(date, re_sect, re_links, re_arttext, re_title, re_author, replace)
except Exception as exc:
    print('Sorry, couldnt run download from ' + url + ' or 0 articles found, error: ')
    print(exc)

#Oila
replace = []
re_links = re.compile('<a href=\"([^"]*?)\" class=\"article__title\">', flags=re.DOTALL)
re_title = re.compile('<meta property=\"og:title\" content=\'([^\']*?)\'>', flags=re.DOTALL)
re_author = re.compile('class=\"date-widget__author\">([^<]*?)</a>', flags=re.DOTALL)
re_arttext = re.compile('<article class=\"wysiwyg page-article__wysiwyg\">(.*?)</article>', flags=re.DOTALL)
#<a class='page-numbers' href='https://khovar.tj/lenta-novostey/page/3924/'>
re_sect = re.compile('class=\"pagination__number\">([^<]*?)</a>', flags=re.DOTALL)
url = "https://oila.tj/"
source = 'Oila'
pre = []    
crawlOila = OilaCr(url, source, pre)
dirs = []
try:
    crawlOila.articles_from_date(date, re_sect, re_links, re_arttext, re_title, re_author, replace)
except Exception as exc:
    print('Sorry, couldnt run download from ' + url + ' or 0 articles found, error: ')
    print(exc)

#Ozodi
replace = []
re_links = re.compile('<div class=\"media-block \">[\n]?<a href=\"([^"]*?)\" class=\"img-wrap img-wrap--t-spac img-wrap--size-[23] img-wrap--float img-wrap', flags=re.DOTALL)
re_title = re.compile('<h1 class=\"title pg-title\" >([^<]*?)</h1>', flags=re.DOTALL)
re_author = re.compile('<title--author\"><a href=\"[^"]*?\">([^<]*?)</a>', flags=re.DOTALL)
re_arttext = re.compile('<div id=\"article-content\" class=\"content-floated-wrap fb-quotable\">(.*?)</div>', flags=re.DOTALL)
url = "https://www.ozodi.org/"
source = 'Ozodi'
pre = []    
crawlOzodi = OzodiCr(url, source, pre)
dirs = []
try:
    crawlOzodi.articles_from_date(date, re_sect, re_links, re_arttext, re_title, re_author, replace)
except Exception as exc:
    print('Sorry, couldnt run download from ' + url + ' or 0 articles found, error: ')
    print(exc)
