import re
import urllib.request
import datetime
import html
import os
from urllib.error import HTTPError
import pandas as pd
import operator
from bs4 import BeautifulSoup
from clean_everything import clean_all

import ssl

context = ssl._create_unverified_context()


phone_number = re.compile('[Тт]?[Ее]?[Лл]?[Ее]?[Фф]?[Оо]?[Нн]?:? ?\(?\+[0-9 ]+\)?[0-9 -]+')
hashtags = re.compile('#[A-zА-яЁёҒӢҚӮҲҶғӣқӯҳҷ]+?')
https = re.compile('\(?https:[/A-z0-9-\?#\.]+\)?')
wwws = re.compile('\(?www\.[/A-z0-9-\?#\.]+\)?')
newlines = re.compile('\n+ +?\n+?')

def basic_subs(text):
    cleaned = phone_number.sub(' ', text)
    cleaned = hashtags.sub('', cleaned)
    cleaned = https.sub('', cleaned)
    cleaned = wwws.sub('', cleaned)
    cleaned = newlines.sub('\n', cleaned)
    cleaned = ('\s+', ' ', cleaned)
    return cleaned.strip(' \n')

class Crawler():
    def __init__(self, url, source, pre_replace=[]):
        self.url = url
        self.source = source
        self.pre_replace = pre_replace

        if not os.path.exists(f'./metadata_{source}.txt'):
            columns = ['filename', 'author', 'title', 'genre', 'year', 'url', 'date', 'source']
            with open(f'./metadata_{source}.txt', 'w', encoding='utf-8') as newmeta:
                newmeta.write('\t'.join(columns))
        with open(f'./metadata_{source}.txt', 'r', encoding='utf-8') as f:
            self.metadf = pd.read_csv(f, header=0, sep='\t', index_col=False, error_bad_lines=False)

    def rpage(self, pageurl):
        hdr = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
            'Accept-Encoding': 'none',
            'Accept-Language': 'en-US,en;q=0.8',
            'Connection': 'keep-alive'}
        print(pageurl)
        req = urllib.request.Request(pageurl, headers=hdr)
        try:
            page = html.unescape(urllib.request.urlopen(req, context=context).read().decode('utf-8'))
        except urllib.error.HTTPError:
            print('urllib.error.HTTPError')
            return None
        #if pageurl == 'https://ovozitojik.uz/news/view?slug=muborakbodixo-ba-halq-va-prezidenti-uzbekiston':
        #    print(page)
        replace = ['<!--.*?-->', '<script.*?</script>', '<style.*?</style>'] + self.pre_replace
        for r in self.pre_replace:
            page = re.sub(r, '', page, flags=re.DOTALL)
        return page

    def meta(self, filename, title, author, year, link, date):
        ''' 1. название файла, 2.автор (если нет,  то пустая ячейка), 3. название статьи, 4. газета
(жанровая характеристика текста - "газета"), 5. год + 6.ссылка 7. дата 8. источник'''
        columns = ['filename', 'author', 'title', 'genre', 'year', 'url', 'date', 'source']
        data = [filename, author, title, "газета", year, link, date, self.source]
        for i, field in enumerate(data):
            data[i] = re.sub("[\r\n\t]", " ", str(field), flags=re.DOTALL)
        new = dict(zip(columns, data))
        self.metadf = self.metadf.append(new, ignore_index=True)
        self.metadf.to_csv(f'./metadata_{self.source}.txt', sep='\t', index=False)
        # with open('./metadata.txt', 'w', encoding = 'utf-8') as oldmeta:
        #    oldmeta.write('\n' + '\t'.join(data))

    def find_filen(self, date):
        n = len(self.metadf[(self.metadf['source'] == self.source) & (self.metadf['date'] == date)])
        return n

    def parse(self, text, articlepage, link, artdate, replace, re_author, date, re_title):
        # print(link)
        for r in replace:
            text = re.sub(r, '', text, flags=re.DOTALL)
        # print(len(text))
        text = re.sub('<.*?>', '', text, flags=re.DOTALL)
        text = re.sub('( ?\r?\n)+', '\r\n', text, flags=re.DOTALL)
        text = re.sub('^\r?\n', '', text, flags=re.DOTALL)
        text = clean_all(text)
        # print(len(text))
        if len(text) != 0:
            n = self.find_filen(artdate) + 1  # порядковый номер новости за день
            # print(str(date))
            filename = str(date) + '-' + str(n)
            path = './' + self.source
            filepath = path + '/' + self.source + '_' + filename + '.txt'
            # print(filepath)
            if not os.path.exists(path):
                try:
                    print("making dir")
                    os.makedirs(path, exist_ok=True)
                except OSError:
                    print("Creation of the directory %s failed" % path)

            if date > datetime.date(year=2023, month=1, day=30):
                with open(filepath, 'w', encoding='utf-8') as articlefile:
                    articlefile.write(text)
                    print("in!")
                    joined_title = ''.join(re_title.findall(articlepage)).replace('\r|\n|\t', '')
                    joined_title = re.sub('ВИДЕО ', '', joined_title).strip('" ')
                    joined_author = ''.join(re_author.findall(articlepage)).replace('\r|\n|\t', '')
                    joined_author = re.sub('\s+', ' ', joined_author)
                    self.meta(filename, joined_title, joined_author, date.year, link, artdate)

    def articles_from_date(self, date, dirs, re_arttext, re_title, re_author, replace):
        artdate = str(date.day) + '.' + str(date.month) + '.' + str(date.year)
        for dir in dirs:
            archive_url = self.url + dir + str(date).replace('-', '') + '/'
            # print(archive_url)
            try:
                page = self.rpage(archive_url)
            except HTTPError as err:
                break
            linkexpruseful = '<a href="/(' + dir + str(date).replace('-', '') + '/[^>]+\.html)">'
            articlenum = re.findall(linkexpruseful, page, flags=re.DOTALL)

            for num in set(articlenum):
                link = self.url + num

                if len(self.metadf[self.metadf['url'] == link]) == 0:
                    articlepage = self.rpage(link)
                    text = '\r\n'.join(re_arttext.findall(articlepage))
                    self.parse(text, articlepage, link=link, artdate=artdate, replace=replace, re_author=re_author,
                               date=date, re_title=re_title)

    def archive(self, start_date, end_date, **kwargs):  # , dirs, re_arttext, re_title, re_author, replace):
        for date in [start_date + datetime.timedelta(days=1 + i) for i in range((end_date - start_date).days)]:
            self.articles_from_date(date, **kwargs)  # , dirs, re_arttext, re_title, re_author, replace)
        # return

    def extract_sections(self, re_sect, re_nav):
        link = self.url
        try:
            page = self.rpage(link)
        except HTTPError as err:
            return []
        #print(page)
        main_nav = re_nav.findall(page)[0]
        # print(main_nav)
        sections = re_sect.findall(main_nav)
        return sections


class FarajCr(Crawler):

    def archive(self, start_date, end_date, **kwargs):
        self.articles_from_date(start_date, end_date)

    def parse(self, link):
        articlepage = self.rpage(link)
        soup = BeautifulSoup(articlepage, 'html.parser')

        artdate = soup.find('time', {'class': "entry-date updated td-module-date"}).text
        re_group = re.search(('(\d+)\.(\d+)\.(\d+)'), artdate)
        date = datetime.date(int(re_group.group(3)), int(re_group.group(2)), int(re_group.group(1)))
        author = soup.find('div', {'class': 'td-author-by'}).text
        textpassages = soup.find('div', {'class': 'td-post-content tagdiv-type'})
        passages = textpassages.findAll('p')
        text = '\r\n'.join([passage.text for passage in passages])
        title = soup.find('h1', {'class': 'entry-title'}).text

        if len(text) != 0:
            n = self.find_filen(artdate) + 1  # порядковый номер новости за день
            # print(str(date))
            filename = str(date) + '-' + str(n)
            path = './' + self.source
            filepath = path + '/' + self.source + '_' + filename + '.txt'
            # print(filepath)
            if not os.path.exists(path):
                try:
                    print("making dir")
                    os.makedirs(path, exist_ok=True)
                except OSError:
                    print("Creation of the directory %s failed" % path)

            if date > datetime.date(year=2023, month=1, day=30):
                with open(filepath, 'w', encoding='utf-8') as articlefile:
                    articlefile.write(text)
                    print("in!")
                    self.meta(filename, title, author, date.year, link, artdate)

    def articles_from_date(self, start_date, end_date):
        years = start_date.year - end_date.year
        yearlinks = [f"https://farazh.tj/{start_date.year-i}/page/1" for i in range(years)]
        for yearlink in yearlinks:
            nextpage = self.rpage(yearlink)
            while nextpage:
                soup = BeautifulSoup(nextpage, 'html.parser')
                div = soup.find('div', {'class': "td-ss-main-content"})
                links = div.findAll('a', {'title': True})
                links = [link['href'] for link in links]

                for link in links:
                    if len(self.metadf[self.metadf['url'] == link]) == 0:

                        articlepage = self.rpage(link)
                        self.parse(link)


                nextpage = div.find('a', {'aria-label':'next-page'})


class OvUzCr(Crawler):

    def archive(self, start_id, end_id, **kwargs):  # , dirs, re_arttext, re_title, re_author, replace):
        self.articles_from_date(start_id, end_id)

    def parse(self, link, page):
        soup = BeautifulSoup(page, 'html.parser')

        artdate = soup.find('time').text
        re_group = re.search(('(\d+)\/(\d+)\/(\d+)'), artdate)
        date = datetime.date(int(re_group.group(3)), int(re_group.group(2)), int(re_group.group(1)))
        author = 'Ovozi Samarqand'#soup.find('div', {'class': 'td-author-by'}).text

        textpassages = soup.find('div', {'class': 'real-content entry-content'})
        passages = textpassages.findAll('p')
        text = '\r\n'.join([passage.text for passage in passages])

        title = soup.find('h1').text

        if len(text) != 0:
            n = self.find_filen(artdate) + 1  # порядковый номер новости за день
            # print(str(date))
            filename = str(date) + '-' + str(n)
            path = './' + self.source
            filepath = path + '/' + self.source + '_' + filename + '.txt'
            # print(filepath)
            if not os.path.exists(path):
                try:
                    print("making dir")
                    os.makedirs(path, exist_ok=True)
                except OSError:
                    print("Creation of the directory %s failed" % path)

            if date > datetime.date(year=2023, month=1, day=30):
                with open(filepath, 'w', encoding='utf-8') as articlefile:
                    articlefile.write(text)
                    print("in!")
                    self.meta(filename, title, author, date.year, link, artdate)

    def articles_from_date(self, start_id, end_id):

        for i in range(end_id-start_id):
            link = f'https://ovozi.uz/{start_id+i}/'
            page = self.rpage(link)
            if page:
                if len(self.metadf[self.metadf['url'] == link]) == 0:
                    try:
                        self.parse(link, page)
                    except:
                        print('NO PAGE', link)



class OvoziCr(Crawler):
    def articles_from_date(self, date, re_date, re_nextpage, re_sect, re_links, re_arttext, re_title, re_author,
                           replace, op=operator.le):
        '''
        set op to  operator.le when downloading all articles from date (e.g. one day download)
        set op to  operator.ge when downloading all articles until date (e.g. archive until a certain date)
        '''

        page = self.rpage(self.url)
        soup = BeautifulSoup(page, 'html.parser')
        article_box = soup.find('div', {'class': 'article-box'})
        dates = re_date.findall(str(article_box))
        dates = [datetime.datetime.strptime(dt, '%d %b %Y').date() for dt in dates]
        lastdate = dates[-1]

        oncemore = iter([True, False])
        #dates = re_date.findall(page)
        #dates = #old
        #lastdate = datetime.datetime.strptime(dates[-1], '%d %b %Y')

        while (len(re_nextpage.findall(page)) != 0 and op(date, lastdate)) or next(oncemore):

            # print(str(date), str(lastdate))
            # print(op(date, lastdate))
            articlelinks = re_links.findall(str(article_box))
            artlinks = []
            for link in articlelinks:
                if re.search('slug', link):
                    artlinks.append(link)
                else:
                    print('IT WENT WRONG', link)
            articlelinks = artlinks
            if op(date, lastdate):
                #print(op(date, lastdate))
                #print(articlelinks)
                for n_art, link in enumerate(articlelinks):
                    print('N', n_art, len(articlelinks))
                    link = self.url + link
                    try:
                        artdate = dates[n_art]
                        artdate_meta = str(artdate.day) + '.' + str(artdate.month) + '.' + str(artdate.year)
                        #### artdate_meta = str(artdate.year) + '-' + str(artdate.month) + '-' + str(artdate.month)
                        n = self.find_filen(artdate_meta)  # порядковый номер новости за день
                        print(n)
                        if len(self.metadf[self.metadf['url'] == link]) == 0:
                            articlepage = self.rpage(link)
                            author = ''.join(re_author.findall(articlepage))
                            text = re_arttext.findall(articlepage)[0]
                            # print(link)
                            self.parse(articlepage, link, artdate_meta, artdate)
                    except IndexError:
                        pass


            next_p = re_nextpage.findall(page)

            if len(next_p) != 0:
                archive_url_p = self.url + next_p[0]
                page = self.rpage(archive_url_p)
                soup = BeautifulSoup(page, 'html.parser')
                article_box = soup.find('div', {'class': 'article-box'})
                dates = re_date.findall(str(article_box))
                dates = [datetime.datetime.strptime(dt, '%d %b %Y').date() for dt in dates]
                lastdate = dates[-1]


    def archive(self, **args):
        self.articles_from_date(**args, op=operator.ge)

    def parse(self, articlepage, link, artdate, date):
        clean = re.compile('[\r\t\xa0 ]+')
        clean_n = re.compile('\n+')
        soup = BeautifulSoup(articlepage, 'html.parser')
        text = soup.find('div', {'class': 'single-post-box'})
        post = text.find('div', {'class': 'post-content'})
        title = clean.sub(' ', text.find('h1').text).strip(' ')
        passages = post.find_all('p')[:-1]
        art = ''
        for p in passages:
            art += p.text + ' '
        art = clean.sub(' ', art).strip(' ')
        art = clean_n.sub('\n', art)
        art = clean_all(art)
        if post.find_all('strong'):
            try:
                author = re.split('[\n,(]', post.find_all('p')[-1].text)[0]
                author = clean.sub(' ', author).strip(' ,-:."')
                if len(author.split(' ')) > 5:
                    author = ''
            except IndexError:
                author = ''
        elif post.find_all('p'):
            if len(post.find_all('p')) > 1:
                try:
                    author = re.split('[,\n(]', post.find_all('p')[-1].text)[0]
                    author = clean.sub(' ', author).strip(' ,.-:"')
                    if len(author.split(' ')) > 5:
                        author = ''
                except IndexError:
                    author = ''
            else:
                author = ''
        else:
            author = ''
        n = self.find_filen(artdate) + 1  # порядковый номер новости за день
        # print(str(date))
        filename = str(date) + '-' + str(n)
        path = './' + self.source
        filepath = path + '/' + self.source + '_' + filename + '.txt'
        # print(filepath)
        if not os.path.exists(path):
            try:
                print("making dir")
                os.makedirs(path, exist_ok=True)
            except OSError:
                print("Creation of the directory %s failed" % path)
        with open(filepath, 'w', encoding='utf-8') as articlefile:
            articlefile.write(art)
            print("in!")
            self.meta(filename, title,
                      author, date.year, link, artdate)

class AsiaCr(Crawler):
    def articles_from_date(self, date, dirs, re_sect, re_links, re_arttext, re_title, re_author, replace):
        # artdate = str(date.year) + '-' + str(date.month) + '-' + str(date.day)
        artdate = str(date.day) + '.' + str(date.month) + '.' + str(date.year)
        n = self.find_filen(artdate)  # порядковый номер новости за день
        # archive_url = 'https://asiaplustj.info/tj/news/all?newsdate=' + '-'.join([str(date.year),str(date.month),str(date.day)])
        archive_url = 'https://asiaplustj.info/tj/news/all?newsdate=' + str(date)
        page = self.rpage(archive_url)
        articlelinks = re_links.findall(page)
        for link in set(articlelinks):
            link = 'https://asiaplustj.info' + link
            if len(self.metadf[self.metadf['url'] == link]) == 0:
                articlepage = self.rpage(link)
                text = '\r\n'.join(re_arttext.findall(articlepage))
                self.parse(text, articlepage, link=link, artdate=artdate, replace=replace, re_author=re_author,
                           date=date, re_title=re_title)
                # print(len(text))

    def archieve(self, date, re_sect, re_links, re_arttext, re_title, re_author, replace):
        #artdate = str(date.year) + '-' + str(date.month) + '-' + str(date.day)
        archive_url = 'https://asiaplustj.info/tj/news/all'
        page_a = self.rpage(archive_url)
        dirs = re_sect.findall(page_a)
        # print(dirs)

        # временный костыль: по какой-то причине краулер считает только 13 первых страниц. нам надо 48
        dirs_range = list(range(1, 113))
        dirs = [f'?page={page}' for page in dirs_range]
        for dir in dirs:
            archive_url_p = archive_url + dir
            print(archive_url)
            page = self.rpage(archive_url_p)
            articlelinks = re_links.findall(page)
            print(len(articlelinks))
            for link in set(articlelinks):
                ext_date = re.findall('/([1-90][1-90][1-90][1-90])([1-90][1-90])([1-90][1-90])/', link, flags=re.DOTALL)
                artdate = ext_date[0][0] + '.' + ext_date[0][1] + '.' + ext_date[0][2]
                date = datetime.date(int(ext_date[0][0]), int(ext_date[0][1]), int(ext_date[0][2]))
                n = self.find_filen(artdate)  # порядковый номер новости за день
                link = 'https://asiaplustj.info' + link
                if len(self.metadf[self.metadf['url'] == link]) == 0:
                    articlepage = self.rpage(link)
                    text = '\r\n'.join(re_arttext.findall(articlepage))
                    self.parse(text, articlepage, link=link, artdate=artdate, replace=replace, re_author=re_author,
                               date=date, re_title=re_title)
                    # print(len(text))


class KhovarCr(Crawler):
    def articles_from_date(self, date, dirs, re_sect, re_links, re_arttext, re_title, re_author, replace):
        # artdate = str(date.year) + '-' + str(date.month) + '-' + str(date.day)
        artdate = str(date.day) + '.' + str(date.month) + '.' + str(date.year)
        n = self.find_filen(artdate)  # порядковый номер новости за день
        # archive_url = 'https://asiaplustj.info/tj/news/all?newsdate=' + '-'.join([str(date.year),str(date.month),str(date.day)])
        archive_url = 'https://khovar.tj/' + str(date.year) + '/' + str(date.month) + '/' + str(date.day)
        page = self.rpage(archive_url)
        articlelinks = re_links.findall(page)
        for link in set(articlelinks):
            if len(self.metadf[self.metadf['url'] == link]) == 0:
                articlepage = self.rpage(link)
                text = '\r\n'.join(re_arttext.findall(articlepage))
                self.parse(text, articlepage, link=link, artdate=artdate, replace=replace, re_author=re_author,
                           date=date, re_title=re_title)
                # print(len(text))

    def parse(self, text, articlepage, link, artdate, replace, author, date, title):
        # print(link)
        for r in replace:
            text = re.sub(r, '', text, flags=re.DOTALL)
        # print(len(text))
        text = re.sub('<.*?>', '', text, flags=re.DOTALL)
        text = re.sub('( ?\r?\n)+', '\r\n', text, flags=re.DOTALL)
        text = re.sub('^\r?\n', '', text, flags=re.DOTALL)
        text = clean_all(text)
        # print(len(text))
        if len(text) != 0:
            n = self.find_filen(artdate) + 1  # порядковый номер новости за день
            # print(str(date))
            filename = str(date) + '-' + str(n)
            path = './' + self.source
            filepath = path + '/' + self.source + '_' + filename + '.txt'
            # print(filepath)
            if not os.path.exists(path):
                try:
                    print("making dir")
                    os.makedirs(path, exist_ok=True)
                except OSError:
                    print("Creation of the directory %s failed" % path)

            if date > datetime.date(year=2021, month=7, day=30):
                with open(filepath, 'w', encoding='utf-8') as articlefile:
                    articlefile.write(text)
                    print("in!")
                    self.meta(filename, title, author, date.year, link, artdate)

    def archieve(self, date, re_sect, re_links, re_arttext, re_title, re_author, replace):
        # artdate = str(date.year) + '-' + str(date.month) + '-' + str(date.day)
        archive_url = 'https://khovar.tj/lenta-novostey/'
        page_a = self.rpage(archive_url)
        dirs = re_sect.findall(page_a)
        last_dir = dirs[-1]
        # print (last_dir)
        for i in range(int(last_dir)):
            pg_num = str(i + 1)
            archive_url_p = 'https://khovar.tj/lenta-novostey/page/' + pg_num + '/'
            print(archive_url_p)
            page = self.rpage(archive_url_p)
            articlelinks = re_links.findall(page)
            for link in set(articlelinks):
                if len(self.metadf[self.metadf['url'] == link]) == 0:
                    articlepage = self.rpage(link)

                    #date
                    soup = BeautifulSoup(articlepage, 'html.parser')
                    article_box = soup.find('div', {'class': 'a-content'})
                    dt = re.search('([A-zА-яЁё]+)[^\d]+(\d+)[^\d]+(\d+)', article_box.text)
                    dt = ' '.join([dt.group(1), dt.group(2), dt.group(3)])
                    date = datetime.datetime.strptime(dt, '%B %d %Y').date()

                    #title
                    try:
                        shareblock = soup.find('div', {'class': 'share-block right'})
                        llink = shareblock.find('a')
                        title = llink['title']
                        print(llink)
                    except:
                        title = soup.find('h1').text

                    artdate = str(date.year) + '.' + str(date.month) + '.' + str(date.day)
                    n = self.find_filen(artdate)  # порядковый номер новости за день
                    textpassages = soup.find('div', {'class': 'content-block main left'})
                    passages = textpassages.findAll('p')
                    text = '\r\n'.join([passage.text for passage in passages])
                    author = re.search('А[Кк][Сс]:?(.+)$', text)
                    if author:
                        text = re.sub(author.group(0), '', text)
                        author = author.group(1).strip(' ')
                    self.parse(text, articlepage, link=link, artdate=artdate, replace=replace, author=author,
                               date=date, title=title)
                    # print(len(text))


class OilaCr(Crawler):
    def articles_from_date(self, date, re_sect, re_links, re_arttext, re_title, re_author, replace):
        date_yst = datetime.date.today() - datetime.timedelta(days=1)
        archive_url = 'https://oila.tj/'
        page_a = self.rpage(archive_url)
        cat = re.findall('<a href=\"([^"]*?)\" class=\"categories-item\">', page_a, flags=re.DOTALL)
        cat.remove('https://oila.tj/category/radio-oila')
        cat.remove('https://oila.tj/category/tv-oila')
        re_data = re.compile(
            '<div class=\"date-widget__time\">[^1-90]*?([1-90][1-90])\.([1-90][1-90])\.([1-90][1-90][1-90][1-90])[^<]*?</div>',
            flags=re.DOTALL)
        # print(cat)
        for c in cat:
            dirs = re_sect.findall(page_a)
            if dirs == []:
                archive_url_p = c
                # print(archive_url_p)
                page = self.rpage(archive_url_p)
                articlelinks = re_links.findall(page)
                for link in set(articlelinks):
                    if len(self.metadf[self.metadf['url'] == link]) == 0:
                        articlepage = self.rpage(link)
                        dt = re_data.findall(articlepage)
                        # print(dt)
                        date = datetime.date(int(dt[0][2]), int(dt[0][1]), int(dt[0][0]))
                        if date == date_yst:
                            artdate = str(date.year) + '.' + str(date.month) + '.' + str(date.day)
                            n = self.find_filen(artdate)  # порядковый номер новости за день
                            text = '\r\n'.join(re_arttext.findall(articlepage))
                            self.parse(text, articlepage, link=link, artdate=artdate, replace=replace,
                                       re_author=re_author, date=date, re_title=re_title)
            else:
                last_dir = dirs[-1]
                print(last_dir)
                for i in range(int(last_dir)):
                    pg_num = str(i + 1)
                    archive_url_p = c + '/page/' + pg_num + '/'
                    # print(archive_url_p)
                    page = self.rpage(archive_url_p)
                    articlelinks = re_links.findall(page)
                    for link in set(articlelinks):
                        if len(self.metadf[self.metadf['url'] == link]) == 0:
                            articlepage = self.rpage(link)
                            dt = re_data.findall(articlepage)
                            # print(dt)
                            date = datetime.date(int(dt[0][2]), int(dt[0][1]), int(dt[0][0]))
                            if date == date_yst:
                                artdate = str(date.year) + '.' + str(date.month) + '.' + str(date.day)
                                n = self.find_filen(artdate)  # порядковый номер новости за день
                                text = '\r\n'.join(re_arttext.findall(articlepage))
                                self.parse(text, articlepage, link=link, artdate=artdate, replace=replace,
                                           re_author=re_author, date=date, re_title=re_title)
                                artdate = str(date.year) + '.' + str(date.month) + '.' + str(date.day)
                                n = self.find_filen(artdate)  # порядковый номер новости за день
                                text = '\r\n'.join(re_arttext.findall(articlepage))
                                self.parse(text, articlepage, link=link, artdate=artdate, replace=replace,
                                           re_author=re_author, date=date, re_title=re_title)
                        # print(len(text))

    def archieve(self, date, re_sect, re_links, re_arttext, re_title, re_author, replace):
        # artdate = str(date.year) + '-' + str(date.month) + '-' + str(date.day)
        archive_url = 'https://oila.tj/'
        page_a = self.rpage(archive_url)
        cat = re.findall('<a href=\"([^"]*?)\" class=\"categories-item\">', page_a, flags=re.DOTALL)
        cat.remove('https://oila.tj/category/radio-oila')
       # cat.remove('https://oila.tj/category/tv-oila') # ValueError: list.remove(x): x not in list
        re_data = re.compile(
            '<div class=\"date-widget__time\">[^1-90]*?([1-90][1-90])\.([1-90][1-90])\.([1-90][1-90][1-90][1-90])[^<]*?</div>',
            flags=re.DOTALL)
        # print(cat)
        for c in cat:
            dirs = re_sect.findall(page_a)
            if dirs == []:
                archive_url_p = c
                print(archive_url_p)
                page = self.rpage(archive_url_p)
                articlelinks = re_links.findall(page)
                for link in set(articlelinks):
                    if len(self.metadf[self.metadf['url'] == link]) == 0:
                        articlepage = self.rpage(link)
                        if articlepage:
                            dt = re_data.findall(articlepage)
                            # print(dt)
                            date = datetime.date(int(dt[0][2]), int(dt[0][1]), int(dt[0][0]))
                            artdate = str(date.year) + '.' + str(date.month) + '.' + str(date.day)
                            n = self.find_filen(artdate)  # порядковый номер новости за день
                            text = '\r\n'.join(re_arttext.findall(articlepage))
                            self.parse(text, articlepage, link=link, artdate=artdate, replace=replace, re_author=re_author,
                                       date=date, re_title=re_title)
            else:
                last_dir = dirs[-1]
                print(last_dir)
                for i in range(int(last_dir)):
                    pg_num = str(i + 1)
                    archive_url_p = c + '/page/' + pg_num + '/'
                    print(archive_url_p)
                    page = self.rpage(archive_url_p)
                    articlelinks = re_links.findall(page)
                    for link in set(articlelinks):
                        if len(self.metadf[self.metadf['url'] == link]) == 0:
                            articlepage = self.rpage(link)
                            dt = re_data.findall(articlepage)
                            # print(dt)
                            date = datetime.date(int(dt[0][2]), int(dt[0][1]), int(dt[0][0]))
                            artdate = str(date.year) + '.' + str(date.month) + '.' + str(date.day)
                            n = self.find_filen(artdate)  # порядковый номер новости за день
                            text = '\r\n'.join(re_arttext.findall(articlepage))
                            self.parse(text, articlepage, link=link, artdate=artdate, replace=replace,
                                       re_author=re_author, date=date, re_title=re_title)
                    # print(len(text))



class OzodiCr(Crawler):
    def archieve(self, date, re_sect, re_links, re_arttext, re_title, re_author, replace):
        # artdate = str(date.year) + '-' + str(date.month) + '-' + str(date.day)
        archive_url = 'https://www.ozodi.org/'
        page_a = self.rpage(archive_url)
        cat = ['https://www.ozodi.org/z/539', 'https://www.ozodi.org/z/16829', 'https://www.ozodi.org/z/542',
              'https://www.ozodi.org/z/543', 'https://www.ozodi.org/z/562', 'https://www.ozodi.org/z/541',
              'https://www.ozodi.org/z/3537', 'https://www.ozodi.org/z/2673']
      # cat = ['https://www.ozodi.org/z/16829']
       # https://www.ozodi.org/z/538
        #links_all = []
        #for c in cat:
        #    page = self.rpage(c)
        #    links_page = re_links.findall(page)
        #    links_all.append(links_page)
        #    i = 0
        #    while links_page != []:
        #        try:
        #            i += 1
        #            url_next = c + '?p=' + str(i)
        #            page = self.rpage(url_next)
        #            links_page = re_links.findall(page)
        #            links_all.append(links_page)
        #        except:
        #            break
        #print(links_all)
        #with open('tajiklinks.txt', 'w', encoding='utf-8') as f:
        #   f.write('\n'.join(links_all))
        with open('links.txt', encoding='utf-8') as f:
            links_all = f.read().splitlines()
        #print(links_all[:100])
        #for links in links_all:
            #for link in links:
        for link in links_all:
            link = 'https://www.ozodi.org' + link
            articlepage = self.rpage(link)
            #try:
            ymd = re.findall(
                'pub_year:\"([1-90][1-90][1-90][1-90])\",pub_month:\"([1-90][1-90])\",pub_day:\"([1-90][1-90])\"',
                articlepage, flags=re.DOTALL)
            date = datetime.date(int(ymd[0][0]), int(ymd[0][1]), int(ymd[0][2]))
            artdate = str(date.year) + '.' + str(date.month) + '.' + str(date.day)
            n = self.find_filen(artdate)  # порядковый номер новости за день
            #text = '\r\n'.join(re_arttext.findall(articlepage))
            #print(articlepage)
            #print('TEXT', text)
            soup = BeautifulSoup(articlepage, 'html.parser')
            #print(soup)
            article_box = soup.find('div', {'class': "content-floated-wrap fb-quotable"})
            if article_box is None:
                article_box = soup.find('div', {'class': "wsw accordeon__target"})

            if article_box is not None:
                passages = article_box.find_all('p')
                passages = [p.text for p in passages]
                text = re.sub('</?p>', '', '\n'.join(passages))
                text = re.sub('Шоҳиди ҳодисае.+', '', text)
                text = re.sub(' ВИДЕО\n', '', text)
                self.parse(text, articlepage, link=link, artdate=artdate, replace=replace, re_author=re_author,
                           date=date, re_title=re_title)
                  #  except:
                 #   pass

    def articles_from_date(self, date, re_sect, re_links, re_arttext, re_title, re_author, replace):
        date_yst = datetime.date.today() - datetime.timedelta(days=1)
        dt_link = str(date_yst.year) + '/' + str(date_yst.month) + '/' + str(date_yst.day)
        cat = ['https://www.ozodi.org/z/539', 'https://www.ozodi.org/z/16829', 'https://www.ozodi.org/z/542',
               'https://www.ozodi.org/z/543', 'https://www.ozodi.org/z/562', 'https://www.ozodi.org/z/541',
               'https://www.ozodi.org/z/3537', 'https://www.ozodi.org/z/2673']
        for c in cat:
            c = c + '/' + dt_link
            # print(c)
            page = self.rpage(c)
            links = re_links.findall(page)
            for link in links:
                link = 'https://www.ozodi.org' + link
                articlepage = self.rpage(link)
                try:
                    ymd = re.findall(
                        'pub_year:\"([1-90][1-90][1-90][1-90])\",pub_month:\"([1-90][1-90])\",pub_day:\"([1-90][1-90])\"',
                        articlepage, flags=re.DOTALL)
                    date = datetime.date(int(ymd[0][0]), int(ymd[0][1]), int(ymd[0][2]))
                    if date < date_yst:
                        break
                    else:
                        artdate = str(date.year) + '.' + str(date.month) + '.' + str(date.day)
                        n = self.find_filen(artdate)  # порядковый номер новости за день
                        text = '\r\n'.join(re_arttext.findall(articlepage))
                        text = re.sub('Шоҳиди ҳодисае.+', '', text)
                        text = re.sub(' ВИДЕО\n', '', stext)
                        text = basic_subs(text)
                        self.parse(text, articlepage, link=link, artdate=artdate, replace=replace, re_author=re_author,
                                   date=date, re_title=re_title)
                except:
                    pass

class crSpTj(Crawler):
    def archive(self, datestop):

        archive_url = 'https://sputnik-tj.com/'
        date = datetime.date(2020,8,1)#datetime.date.today()
        datelinks = []
        for i in range((date - datestop).days):
            datelinks.append(archive_url + str(date - datetime.timedelta(days=i)).replace('-',''))

        for datelink in datelinks:
            page_a = self.rpage(datelink)
            soup = BeautifulSoup(page_a, 'html.parser')
            linksblock = soup.find('div', {'class': 'list list-tag'})
            alinks = linksblock.findAll('a', {'class': 'list__title'})
            allinks = []
            for link in alinks:
                if link['href'].endswith('.html'):
                    allinks.append(link)
            alinks = [archive_url + link['href'] for link in allinks]
            for link in alinks:
                articlepage = self.rpage(link)
                soup = BeautifulSoup(articlepage, 'html.parser')
                meta = soup.find('div', {'class':'article__info-date'})
                title = soup.find('h1').text
                # artdate = meta.find('a').text.split(' ')[1]
                artdate = datelink.split('/')[-1]
                artdate = artdate[6:]  + '.' + artdate[4:6] + '.' + artdate[:4]
                date = datetime.datetime.strptime(artdate, '%d.%m.%Y').date() #17.01.2021
             #  n = self.find_filen(artdate)  # порядковый номер новости за день

                article_box = soup.find('div', {'class': "article__body"})
                passages = article_box.find_all('div', {'class':'article__block',
                                                        'data-type':'text'})
                passages = [p.text for p in passages]
                text = re.sub('</?p>', '', '\n'.join(passages))
                text = re.sub('Шоҳиди ҳодисае.+', '', text)
                text = re.sub(' ВИДЕО\n', '', text)
                self.parse(text, link=link, artdate=artdate, author='',
                           date=date, title=title)

    def parse(self, text, link, artdate, author, date, title):
        # print(link)
        text = re.sub('<.*?>', '', text, flags=re.DOTALL)
        text = re.sub('( ?\r?\n)+', '\r\n', text, flags=re.DOTALL)
        text = re.sub('^\r?\n', '', text, flags=re.DOTALL)
        text = clean_all(text)

        if len(text) != 0:
            n = self.find_filen(artdate) + 1  # порядковый номер новости за день

            filename = str(date) + '-' + str(n)
            path = './' + self.source
            filepath = path + '/' + self.source + '_' + filename + '.txt'
            if not os.path.exists(path):
                try:
                    print("making dir")
                    os.makedirs(path, exist_ok=True)
                except OSError:
                    print("Creation of the directory %s failed" % path)

            if date > datetime.date(year=2020, month=7, day=14):
                with open(filepath, 'w', encoding='utf-8') as articlefile:
                    articlefile.write(text)
                    print("in!")
                    self.meta(filename, title, author, date.year, link, artdate)
