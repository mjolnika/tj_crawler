import re
import urllib.request
import datetime
import html
import os
from urllib.error import HTTPError
import pandas as pd
import operator
import locale
from changed_classes import *

locale.setlocale(locale.LC_ALL, 'tg_TJ.UTF8')

if __name__ == '__main__':
     date = datetime.date.today() - datetime.timedelta(days=1)
     start_date = datetime.date(2023, 1, 29)

     #Sputnik Taj
     url = "https://sputnik-tj.com/"
     source = 'Sputnik Таджикистан'
     crawlSpTj = crSpTj(url='', source='sputnik_tajikistan')
     crawlSpTj.archive(datetime.date(2023, 1, 29))

     # ovozi uz
     url = "https://ovozi.uz/"
     source = 'ovozi_samarqand'
     pre = []
     dirs = []
     crawlOvUz = OvUzCr(url, source, pre)
     crawlOvUz.archive(start_id=39207, end_id=39630)

     #Faraj (New)
     url = "https://farazh.tj/"
     source = 'farazh'
     pre = []
     dirs = []
     crawlFar = FarajCr(url, source, pre)
     crawlFar.archive(start_date=datetime.date.today(), end_date=datetime.date(2023, 1, 29))

     #Ovozi
      replace = ['© 2012-2018 \"OvoziTojik.uz\"   Все права защищены.']
      re_links = re.compile('<h2><a href="(.*?)"', flags=re.DOTALL)
      re_nextpage = re.compile('<li class=\"next\"><a href=\"(.*?)\"', flags=re.DOTALL)
      re_title = re.compile('<h1>(.*?)</h1>', flags=re.DOTALL)
      re_author = re.compile('<strong>.*?([А-ЯҶҒҚӮҲЭ][^ ]*? ?[А-ЯҶҒҚӮҲЭ]{3}[А-ЯҶҒҚӮҲЭ]*).*?</strong>', flags=re.DOTALL)
      #<strong>К. САЛОМОВ,<br />\r\nомӯзгори фанни таърих.</strong>
      # <i class="fa fa-clock-o"></i>29 Сен 2020 </li>
      re_date = re.compile('<i class="fa fa-clock-o"></i> ?([0-9 ИМаюДйтАлФСпровяекснОНгЯ]*?) ?</li>', flags=re.DOTALL)
      re_arttext = re.compile('<p>.*?</p>', flags=re.DOTALL)
      url = 'https://ovozitojik.uz'
      source = 'ovozi_tojik'
      #yesterday = datetime.date.today() - datetime.timedelta(days=1)
      date = datetime.date.today() - datetime.timedelta(days=1)
      pre = []
      #dirs = []
      ovCrawl = OvoziCr(url, source, pre)
      re_sect = re.compile('class=\"last\" title=\"[1-9]*?\">', flags=re.DOTALL)
      ovCrawl.archive(date=date, re_date=re_date, re_nextpage=re_nextpage, re_sect=re_sect,
                      re_links=re_links, re_arttext=re_arttext, re_title=re_title,
                     re_author=re_author, replace=replace)

     #AsiaPlusTj
     replace = []
     re_links = re.compile('<div><a href=\"([^"]*?)\"><h3>', flags=re.DOTALL)
     re_title = re.compile('<h1 class=\"atitle\"  >(.*?)</h1>', flags=re.DOTALL)
     re_author = re.compile('<span class=\'article-author\'>(.*?)</span>', flags=re.DOTALL)
     re_arttext = re.compile('<div class=\'article-body js-mediator-article\'>(.*?)<script class=', flags=re.DOTALL)
     url = "https://asiaplustj.info/tj/news/all"
     source = 'asia_plus'
     pre = []
     crawlAsia = AsiaCr(url, source, pre)
     dirs = []
     re_sect = re.compile('<a href=\'/tj/news/all([?]page=[1-9]*?)\'', flags=re.DOTALL)
     # date, re_sect, re_links, re_arttext, re_title, re_author, replace
     crawlAsia.archieve(date,  re_sect, re_links, re_arttext, re_title, re_author, replace)

     ##Khovar
     #locale.setlocale(locale.LC_ALL, 'ru_RU.UTF8')
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
     #crawlKhovar.archieve(date, re_sect, re_links, re_arttext, re_title, re_author, replace)

     try:
         crawlKhovar.archieve(date, re_sect, re_links, re_arttext, re_title, re_author, replace)
     except:
         print('Sorry, couldnt run download from ' + url + ' or 0 articles found')

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
     crawlOila.archieve(date, re_sect, re_links, re_arttext, re_title, re_author, replace)

        #Ozodi
     date = datetime.date.today() - datetime.timedelta(days=1)
     replace = []
     re_links = re.compile('<div class=\"media-block \">[\n]?<a href=\"([^"]*?)\" class=\"img-wrap img-wrap--t-spac img-wrap--size-[23] img-wrap--float img-wrap', flags=re.DOTALL)
     re_title = re.compile('<h1 class=\"title pg-title\" >([^<]*?)</h1>', flags=re.DOTALL)
     re_author = re.compile('<title--author\"><a href=\"[^"]*?\">([^<]*?)</a>', flags=re.DOTALL) #
     re_arttext = re.compile('<div class="wsw accordeon__target">(.*?)</div>', flags=re.DOTALL)
     #<a class='page-numbers' href='https://khovar.tj/lenta-novostey/page/3924/'>
     re_sect = re.compile('<a class="handler" href=\"([^"]*?)\">', flags=re.DOTALL)
     url = "https://www.ozodi.org/"
     source = 'Ozodi'
     pre = []
     crawlOzodi = OzodiCr(url, source, pre)
     dirs = []
     crawlOzodi.archieve(date, re_sect, re_links, re_arttext, re_title, re_author, replace)