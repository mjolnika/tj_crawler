import re
import urllib.request
import datetime
import html
import os
from urllib.error import HTTPError
import pandas as pd
import operator

class Crawler():
    def __init__(self, url, source, pre_replace=[]):
        self.url = url
        self.source = source
        self.pre_replace = pre_replace
        
        if not os.path.exists('./metadata.txt'):    
            columns = ['filename', 'author', 'title', 'genre','year', 'url', 'date', 'source']
            with open('./metadata.txt', 'w', encoding='utf-8') as newmeta:
                newmeta.write('\t'.join(columns))                
        with open('./metadata.txt', 'r', encoding='utf-8') as f:
            self.metadf = pd.read_csv(f, header=0, sep='\t', index_col=False, error_bad_lines=False)


        
    def rpage(self, pageurl):
        hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
               'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
               'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
               'Accept-Encoding': 'none',
               'Accept-Language': 'en-US,en;q=0.8',
               'Connection': 'keep-alive'}
        print(pageurl)
        req = urllib.request.Request(pageurl, headers=hdr)
        page = html.unescape(urllib.request.urlopen(req).read().decode('utf-8'))
        
        replace=['<!--.*?-->','<script.*?</script>', '<style.*?</style>' ]+self.pre_replace
        for r in self.pre_replace:
            page = re.sub(r, '', page, flags=re.DOTALL)
        return page


    def meta(self, filename, title, author, year, link, date):
        ''' 1. название файла, 2.автор (если нет,  то пустая ячейка), 3. название статьи, 4. газета
(жанровая характеристика текста - "газета"), 5. год + 6.ссылка 7. дата 8. источник'''
        columns = ['filename', 'author', 'title', 'genre','year', 'url', 'date', 'source']
        data = [filename, author, title, "газета", year, link, date, self.source ]
        for i, field in enumerate(data):
            data[i] = re.sub("[\r\n\t]", " ", str(field), flags=re.DOTALL)        
        new =  dict(zip(columns, data))  
        self.metadf = self.metadf.append(new, ignore_index=True)
        self.metadf.to_csv('./metadata.txt', sep='\t', index=False)
        #with open('./metadata.txt', 'w', encoding = 'utf-8') as oldmeta:    
        #    oldmeta.write('\n' + '\t'.join(data))
        
    def find_filen(self, date):
        n = len(self.metadf[(self.metadf['source']==self.source)&(self.metadf['date']==date)])   
        return n
    
    def parse(self, text, articlepage, link, artdate, replace, re_author,date,re_title):
        #print(link)
        for r in replace:
            text = re.sub(r, '', text,flags=re.DOTALL)
        #print(len(text))
        text = re.sub('<.*?>', '', text,flags=re.DOTALL)
        text = re.sub('( ?\r?\n)+', '\r\n', text,flags=re.DOTALL)
        text = re.sub('^\r?\n', '', text,flags=re.DOTALL)
        #print(len(text))
        if len(text) != 0:
            n = self.find_filen(artdate) + 1 #порядковый номер новости за день
            #print(str(date))
            filename = str(date) + '-' + str(n)
            path = './' + self.source
            filepath =  path + '/' + filename + '.txt'
            #print(filepath)   
            if not os.path.exists(path):
                try:
                    print("making dir")
                    os.makedirs(path, exist_ok=True)
                except OSError:
                    print ("Creation of the directory %s failed" % path)

            with open (filepath, 'w', encoding = 'utf-8') as articlefile:
                articlefile.write(text)
                print("in!")
                self.meta(filename, (''.join(re_title.findall(articlepage))).replace('\r|\n|\t',''),
                 (''.join(re_author.findall(articlepage))).replace('\r|\n|\t',''), date.year, link, artdate)

            
    def articles_from_date(self, date, dirs, re_arttext, re_title, re_author, replace):
        artdate = str(date.day) + '.' + str(date.month) + '.' + str(date.year)
        
                    
        for dir in dirs:
            archive_url = self.url + dir +  str(date).replace('-', '') + '/'
            #print(archive_url)
            try:
                page = self.rpage(archive_url)
            except HTTPError as err:
                break
            linkexpruseful = '<a href="/(' + dir + str(date).replace('-', '') + '/[^>]+\.html)">'
            articlenum = re.findall(linkexpruseful, page, flags=re.DOTALL)
            
            for num in set(articlenum):
                link= self.url + num
                
                if len(self.metadf[self.metadf['url']==link]) == 0:
                    articlepage = self.rpage(link)                    
                    text = '\r\n'.join(re_arttext.findall(articlepage))
                    self.parse(text, articlepage, link=link, artdate=artdate, replace=replace, re_author=re_author,date=date,re_title=re_title)
                    
    
    def archive(self, start_date, end_date, **kwargs):#, dirs, re_arttext, re_title, re_author, replace):
        for date in [start_date+datetime.timedelta(days=1+i) for i in range((end_date-start_date).days)]:           
            self.articles_from_date(date, **kwargs)#, dirs, re_arttext, re_title, re_author, replace)
        #return 
        
    def extract_sections(self, re_sect, re_nav):
        link= self.url
        try:
            page = self.rpage(link)
        except HTTPError as err:
            return []
        
        main_nav = re_nav.findall(page)[0]
        #print(main_nav)
        sections =  re_sect.findall(main_nav)       
        return sections                            


class FarajCr(Crawler):
    def articles_from_date(self, date, re_sect, re_links, dirs, re_arttext, re_title, re_author, replace):
        artdate = str(date.day) + '.' + str(date.month) + '.' + str(date.year)
        n = self.find_filen(artdate) #порядковый номер новости за день
        archive_url = self.url + '/'.join([str(date.year),str(date.month),str(date.day)]) + '/' 
        dirs = self.extract_sections(archive_url, re_sect)
#         print(dirs)
        for dir in dirs:
            archive_url_p = archive_url + dir
            #print(archive_url)
            page = self.rpage(archive_url_p)

            #linkexpruseful = #'<a href="/(' + dir + str(date).replace('-', '') + '/[^>]+\.html)">'
            articlelinks = re_links.findall(page)
            
            for link in set(articlelinks):               
                            
                if len(self.metadf[self.metadf['url']==link]) == 0:
                    articlepage = self.rpage(link)
                    
                    text = '\r\n'.join(re_arttext.findall(articlepage))
                    self.parse(text, articlepage, link=link, artdate=artdate, replace=replace, re_author=re_author,date=date,re_title=re_title)
                    #print(len(text))
     
    
    def extract_sections(self, link, re_sect):  
        try:
            page = self.rpage(link)
        except HTTPError as err:
            return []
        if len(re_sect.findall(page)) == 0:
            max_p=1
        else:    
            max_p = int(re_sect.findall(page)[0])

        sections =  ['page/'+str(i) for i in range(1,max_p+1)]   
        return sections     
    

class OvoziCr(Crawler):
    def articles_from_date(self, date, re_date, re_nextpage, re_sect, re_links, re_arttext, re_title, re_author, replace, op=operator.le):
        '''
        set op to  operator.le when downloading all articles from date (e.g. one day download)
        set op to  operator.ge when downloading all articles untill date (e.g. archive untill a certain date) '''

        page = self.rpage(self.url)
        oncemore = iter([True, False])
        dates = re_date.findall(page)
        lastdate = datetime.date(*map(int, dates[-1].split('-')))
        
        while (len(re_nextpage.findall(page)) != 0 and op(date, lastdate)) or next(oncemore):
            
            #print(str(date), str(lastdate))
            #print(op(date, lastdate))
            articlelinks = re_links.findall(page)
            if op(date, lastdate):
                for n_art, link in enumerate(articlelinks):
                    link = self.url+link
                    artdate = datetime.date(*map(int, dates[n_art].split('-')))
                    artdate_meta = str(artdate.day) + '.' + str(artdate.month) + '.' + str(artdate.year)
                    #n = self.find_filen(artdate_meta) #порядковый номер новости за день
                                
                    if len(self.metadf[self.metadf['url']==link]) == 0:                    
                        articlepage = self.rpage(link)
                        author = ''.join(re_author.findall(articlepage))
                        text = re_arttext.findall(articlepage)[0]
                        #print(link)
                        self.parse(text, articlepage,link=link, artdate=artdate_meta, replace=replace, re_author=re_author, date=artdate, re_title=re_title)
            
            
            next_p = re_nextpage.findall(page)            
            
            if len(next_p) != 0:
                archive_url_p = self.url + next_p[0]
                page = self.rpage(archive_url_p)
                dates = re_date.findall(page)
                lastdate = datetime.date(*map(int, dates[-1].split('-')))
            
                
    def archive(self, **args):
        self.articles_from_date(**args, op=operator.ge)


 
#"http://khovar.tj/"
#"https://ovozisamarqand.uz/"
#"https://oila.tj/"
#"https://asiaplustj.info/"
#"https://akhbor.com/"

#https://asiaplustj.info/tj/news/all?newsdate=2020-06-16

class AsiaCr(Crawler):
    def articles_from_date(self, date, dirs, re_sect, re_links, re_arttext, re_title, re_author, replace):
        #artdate = str(date.year) + '-' + str(date.month) + '-' + str(date.day)
        artdate = str(date.day) + '.' + str(date.month) + '.' + str(date.year)
        n = self.find_filen(artdate) #порядковый номер новости за день
        #archive_url = 'https://asiaplustj.info/tj/news/all?newsdate=' + '-'.join([str(date.year),str(date.month),str(date.day)])
        archive_url = 'https://asiaplustj.info/tj/news/all?newsdate=' + str(date)
        page = self.rpage(archive_url)
        articlelinks = re_links.findall(page)     
        for link in set(articlelinks):
            link = 'https://asiaplustj.info' + link 
            if len(self.metadf[self.metadf['url']==link]) == 0:
                articlepage = self.rpage(link)
                text = '\r\n'.join(re_arttext.findall(articlepage))
                self.parse(text, articlepage, link=link, artdate=artdate, replace=replace, re_author=re_author,date=date,re_title=re_title)
                #print(len(text))
                    
    def archieve(self, date, re_sect, re_links, re_arttext, re_title, re_author, replace):
        #artdate = str(date.year) + '-' + str(date.month) + '-' + str(date.day)
        archive_url = 'https://asiaplustj.info/tj/news/all'
        page_a = self.rpage(archive_url)
        dirs = re_sect.findall(page_a)
        #print(dirs)
        for dir in dirs:
            archive_url_p = archive_url + dir
            print(archive_url)
            page = self.rpage(archive_url_p)
            articlelinks = re_links.findall(page)
            for link in set(articlelinks):
                ext_date = re.findall('/([1-90][1-90][1-90][1-90])([1-90][1-90])([1-90][1-90])/', link, flags=re.DOTALL)
                artdate = ext_date[0][0] + '.' + ext_date[0][1] + '.' + ext_date[0][2]
                date = datetime.date(int(ext_date[0][0]), int(ext_date[0][1]), int(ext_date[0][2]))
                n = self.find_filen(artdate) #порядковый номер новости за день
                link = 'https://asiaplustj.info' + link          
                if len(self.metadf[self.metadf['url']==link]) == 0:
                    articlepage = self.rpage(link)
                    text = '\r\n'.join(re_arttext.findall(articlepage))
                    self.parse(text, articlepage, link=link, artdate=artdate, replace=replace, re_author=re_author,date=date,re_title=re_title)
                    #print(len(text))
             
class KhovarCr(Crawler):
    def articles_from_date(self, date, dirs, re_sect, re_links, re_arttext, re_title, re_author, replace):
        #artdate = str(date.year) + '-' + str(date.month) + '-' + str(date.day)
        artdate = str(date.day) + '.' + str(date.month) + '.' + str(date.year)
        n = self.find_filen(artdate) #порядковый номер новости за день
        #archive_url = 'https://asiaplustj.info/tj/news/all?newsdate=' + '-'.join([str(date.year),str(date.month),str(date.day)])
        archive_url = 'https://khovar.tj/' + str(date.year) + '/' + str(date.month) + '/' + str(date.day)
        page = self.rpage(archive_url)
        articlelinks = re_links.findall(page)     
        for link in set(articlelinks):
            if len(self.metadf[self.metadf['url']==link]) == 0:
                articlepage = self.rpage(link)
                text = '\r\n'.join(re_arttext.findall(articlepage))
                self.parse(text, articlepage, link=link, artdate=artdate, replace=replace, re_author=re_author,date=date,re_title=re_title)
                #print(len(text))
                    
    def archieve(self, date, re_sect, re_links, re_arttext, re_title, re_author, replace):
        #artdate = str(date.year) + '-' + str(date.month) + '-' + str(date.day)
        archive_url = 'https://khovar.tj/lenta-novostey/'
        page_a = self.rpage(archive_url)
        dirs = re_sect.findall(page_a)
        last_dir = dirs[-1]
        #print (last_dir)
        for i in range(int(last_dir)):
            pg_num = str(i + 1)
            archive_url_p = 'https://khovar.tj/lenta-novostey/page/' + pg_num + '/'
            print(archive_url_p)
            page = self.rpage(archive_url_p)
            articlelinks = re_links.findall(page)
            for link in set(articlelinks):    
                if len(self.metadf[self.metadf['url']==link]) == 0:
                    articlepage = self.rpage(link)
                    day = re.findall('<div class="a-content"> <span class="meta">[^1-90]*?([1-90]*?),[^<]*?</span>', articlepage, flags=re.DOTALL)
                    yyyymm = re.findall('khovar.tj/([1-90][1-90][1-90][1-90])/([1-90][1-90])/', link, flags=re.DOTALL)
                    date = datetime.date(int(yyyymm[0][0]), int(yyyymm[0][1]), int(day[0]))
                    artdate = str(date.year) + '.' + str(date.month) + '.' + str(date.day)
                    n = self.find_filen(artdate) #порядковый номер новости за день  
                    text = '\r\n'.join(re_arttext.findall(articlepage))
                    self.parse(text, articlepage, link=link, artdate=artdate, replace=replace, re_author=re_author,date=date,re_title=re_title)
                    #print(len(text))
             

class OilaCr(Crawler):
    def articles_from_date(self, date, re_sect, re_links, re_arttext, re_title, re_author, replace):
        date_yst = datetime.date.today() - datetime.timedelta(days=1)
        archive_url = 'https://oila.tj/'
        page_a = self.rpage(archive_url)
        cat = re.findall('<a href=\"([^"]*?)\" class=\"categories-item\">', page_a,flags=re.DOTALL)
        cat.remove('https://oila.tj/category/radio-oila')
        cat.remove('https://oila.tj/category/tv-oila')
        re_data = re.compile('<div class=\"date-widget__time\">[^1-90]*?([1-90][1-90])\.([1-90][1-90])\.([1-90][1-90][1-90][1-90])[^<]*?</div>', flags=re.DOTALL)
        #print(cat)
        for c in cat:
            dirs = re_sect.findall(page_a)
            if dirs == []:
                archive_url_p = c
                #print(archive_url_p)
                page = self.rpage(archive_url_p)
                articlelinks = re_links.findall(page)
                for link in set(articlelinks):
                    if len(self.metadf[self.metadf['url']==link]) == 0:
                        articlepage = self.rpage(link)
                        dt = re_data.findall(articlepage)
                        #print(dt)
                        date = datetime.date(int(dt[0][2]), int(dt[0][1]), int(dt[0][0]))
                        if date == date_yst:
                            artdate = str(date.year) + '.' + str(date.month) + '.' + str(date.day)
                            n = self.find_filen(artdate) #порядковый номер новости за день  
                            text = '\r\n'.join(re_arttext.findall(articlepage))
                            self.parse(text, articlepage, link=link, artdate=artdate, replace=replace, re_author=re_author,date=date,re_title=re_title)
            else:
                last_dir = dirs[-1]
                print (last_dir)
                for i in range(int(last_dir)):
                    pg_num = str(i + 1)
                    archive_url_p = c + '/page/' + pg_num + '/'
                    #print(archive_url_p)
                    page = self.rpage(archive_url_p)
                    articlelinks = re_links.findall(page)
                    for link in set(articlelinks):
                        if len(self.metadf[self.metadf['url']==link]) == 0:
                            articlepage = self.rpage(link)
                            dt = re_data.findall(articlepage)
                            #print(dt)
                            date = datetime.date(int(dt[0][2]), int(dt[0][1]), int(dt[0][0]))
                            if date == date_yst:
                                artdate = str(date.year) + '.' + str(date.month) + '.' + str(date.day)
                                n = self.find_filen(artdate) #порядковый номер новости за день  
                                text = '\r\n'.join(re_arttext.findall(articlepage))
                                self.parse(text, articlepage, link=link, artdate=artdate, replace=replace, re_author=re_author,date=date,re_title=re_title)
                                artdate = str(date.year) + '.' + str(date.month) + '.' + str(date.day)
                                n = self.find_filen(artdate) #порядковый номер новости за день  
                                text = '\r\n'.join(re_arttext.findall(articlepage))
                                self.parse(text, articlepage, link=link, artdate=artdate, replace=replace, re_author=re_author,date=date,re_title=re_title)
                        #print(len(text))
                    
    def archieve(self, date, re_sect, re_links, re_arttext, re_title, re_author, replace):
        #artdate = str(date.year) + '-' + str(date.month) + '-' + str(date.day)
        archive_url = 'https://oila.tj/'
        page_a = self.rpage(archive_url)
        cat = re.findall('<a href=\"([^"]*?)\" class=\"categories-item\">', page_a,flags=re.DOTALL)
        cat.remove('https://oila.tj/category/radio-oila')
        cat.remove('https://oila.tj/category/tv-oila')
        re_data = re.compile('<div class=\"date-widget__time\">[^1-90]*?([1-90][1-90])\.([1-90][1-90])\.([1-90][1-90][1-90][1-90])[^<]*?</div>', flags=re.DOTALL)
        #print(cat)
        for c in cat:
            dirs = re_sect.findall(page_a)
            if dirs == []:
                archive_url_p = c
                print(archive_url_p)
                page = self.rpage(archive_url_p)
                articlelinks = re_links.findall(page)
                for link in set(articlelinks):
                    if len(self.metadf[self.metadf['url']==link]) == 0:
                        articlepage = self.rpage(link)
                        dt = re_data.findall(articlepage)
                        #print(dt)
                        date = datetime.date(int(dt[0][2]), int(dt[0][1]), int(dt[0][0]))
                        artdate = str(date.year) + '.' + str(date.month) + '.' + str(date.day)
                        n = self.find_filen(artdate) #порядковый номер новости за день  
                        text = '\r\n'.join(re_arttext.findall(articlepage))
                        self.parse(text, articlepage, link=link, artdate=artdate, replace=replace, re_author=re_author,date=date,re_title=re_title)
            else:
                last_dir = dirs[-1]
                print (last_dir)
                for i in range(int(last_dir)):
                    pg_num = str(i + 1)
                    archive_url_p = c + '/page/' + pg_num + '/'
                    print(archive_url_p)
                    page = self.rpage(archive_url_p)
                    articlelinks = re_links.findall(page)
                    for link in set(articlelinks):
                        if len(self.metadf[self.metadf['url']==link]) == 0:
                            articlepage = self.rpage(link)
                            dt = re_data.findall(articlepage)
                            #print(dt)
                            date = datetime.date(int(dt[0][2]), int(dt[0][1]), int(dt[0][0]))
                            artdate = str(date.year) + '.' + str(date.month) + '.' + str(date.day)
                            n = self.find_filen(artdate) #порядковый номер новости за день  
                            text = '\r\n'.join(re_arttext.findall(articlepage))
                            self.parse(text, articlepage, link=link, artdate=artdate, replace=replace, re_author=re_author,date=date,re_title=re_title)
                    #print(len(text))
             



class OvoziSamCr(Crawler):
    def archieve(self, date, re_sect, re_links, re_arttext, re_title, re_author, replace):
        #artdate = str(date.year) + '-' + str(date.month) + '-' + str(date.day)
        archive_url = 'https://ovozisamarqand.uz/?cat=1'
        for i in range(1, 274):
            page_url = archive_url + '&paged=' + str(i)
            page = self.rpage(page_url)
            articlelinks = re_links.findall(page)
            for link in set(articlelinks):    
                if len(self.metadf[self.metadf['url']==link]) == 0:
                    articlepage = self.rpage(link)
                    day = re.findall('<i class=\"icon-clock\" aria-hidden=\"true\"></i>([1-90]*?) [а-яё]', articlepage, flags=re.DOTALL)
                    yyyymm = re.findall('\"https://ovozisamarqand.uz/wp-content/uploads/([1-90][1-90][1-90][1-90])/([1-90][1-90])/', articlepage, flags=re.DOTALL)[-1]
                    date = datetime.date(int(yyyymm[0]), int(yyyymm[1]), int(day[0]))
                    artdate = str(date.year) + '.' + str(date.month) + '.' + str(date.day)
                    #print(artdate)
                    n = self.find_filen(artdate) #порядковый номер новости за день  
                    text = '\r\n'.join(re_arttext.findall(articlepage))
                    self.parse(text, articlepage, link=link, artdate=artdate, replace=replace, re_author=re_author,date=date,re_title=re_title)
    def articles_from_date(self, date, re_sect, re_links, re_arttext, re_title, re_author, replace):
        date_yst = datetime.date.today() - datetime.timedelta(days=1)
        archive_url = 'https://ovozisamarqand.uz/?cat=1'
        for i in range(1, 274):
            page_url = archive_url + '&paged=' + str(i)
            page = self.rpage(page_url)
            articlelinks = re_links.findall(page)
            if date < date_yst:
                break
            for link in set(articlelinks):    
                if len(self.metadf[self.metadf['url']==link]) == 0:
                    articlepage = self.rpage(link)
                    day = re.findall('<i class=\"icon-clock\" aria-hidden=\"true\"></i>([1-90]*?) [а-яё]', articlepage, flags=re.DOTALL)
                    yyyymm = re.findall('\"https://ovozisamarqand.uz/wp-content/uploads/([1-90][1-90][1-90][1-90])/([1-90][1-90])/', articlepage, flags=re.DOTALL)[-1]
                    date = datetime.date(int(yyyymm[0]), int(yyyymm[1]), int(day[0]))
                    artdate = str(date.year) + '.' + str(date.month) + '.' + str(date.day)
                    if date == date_yst:
                        n = self.find_filen(artdate) #порядковый номер новости за день  
                        text = '\r\n'.join(re_arttext.findall(articlepage))
                        self.parse(text, articlepage, link=link, artdate=artdate, replace=replace, re_author=re_author,date=date,re_title=re_title)

class OzodiCr(Crawler):
    def archieve(self, date, re_sect, re_links, re_arttext, re_title, re_author, replace):
        #artdate = str(date.year) + '-' + str(date.month) + '-' + str(date.day)
        archive_url = 'https://www.ozodi.org/'
        page_a = self.rpage(archive_url)
        cat = ['https://www.ozodi.org/z/539', 'https://www.ozodi.org/z/16829', 'https://www.ozodi.org/z/542',
               'https://www.ozodi.org/z/543', 'https://www.ozodi.org/z/562', 'https://www.ozodi.org/z/541',
               'https://www.ozodi.org/z/3537', 'https://www.ozodi.org/z/2673']
        #https://www.ozodi.org/z/538
        links_all = []
        for c in cat:
            page = self.rpage(c)
            links_page = re_links.findall(page)
            links_all.append(links_page)
            i = 0
            while links_page != []:
                try:
                    i += 1
                    url_next = c + '?p=' + str(i)
                    page = self.rpage(url_next)
                    links_page = re_links.findall(page)
                    links_all.append(links_page)
                except:
                    break
            #print(links_all)
        for links in links_all:
            for link in links:
                link = 'https://www.ozodi.org' + link
                articlepage = self.rpage(link)
                try:
                    ymd = re.findall('pub_year:\"([1-90][1-90][1-90][1-90])\",pub_month:\"([1-90][1-90])\",pub_day:\"([1-90][1-90])\"', articlepage, flags=re.DOTALL)
                    date = datetime.date(int(ymd[0][0]), int(ymd[0][1]), int(ymd[0][2]))
                    artdate = str(date.year) + '.' + str(date.month) + '.' + str(date.day)
                    n = self.find_filen(artdate) #порядковый номер новости за день  
                    text = '\r\n'.join(re_arttext.findall(articlepage))
                    self.parse(text, articlepage, link=link, artdate=artdate, replace=replace, re_author=re_author,date=date,re_title=re_title)
                except:
                    pass

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
                    ymd = re.findall('pub_year:\"([1-90][1-90][1-90][1-90])\",pub_month:\"([1-90][1-90])\",pub_day:\"([1-90][1-90])\"', articlepage, flags=re.DOTALL)
                    date = datetime.date(int(ymd[0][0]), int(ymd[0][1]), int(ymd[0][2]))
                    if date < date_yst:
                        break
                    else:
                        artdate = str(date.year) + '.' + str(date.month) + '.' + str(date.day)
                        n = self.find_filen(artdate) #порядковый номер новости за день  
                        text = '\r\n'.join(re_arttext.findall(articlepage))
                        self.parse(text, articlepage, link=link, artdate=artdate, replace=replace, re_author=re_author,date=date,re_title=re_title)
                except:
                    pass

        
