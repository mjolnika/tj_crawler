import re
from string import punctuation

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
    cleaned = re.sub('\s+', ' ', cleaned)
    return cleaned.strip(' \n')

def subs(text):
    text = text.replace('ў', 'ӯ')
    text = text.replace('COVID-19', 'COVID-19 ')
    text = re.sub('\\+ ?[0-9]+( [0-9]+)+', ' ', text)
    text = re.sub('h?ttps?:\\/\\/[^ ]+', ' ', text)
    text = re.sub('[A-z0-9-]+_[A-z0-9-]+', ' ', text)
    text = re.sub('(\\w+)_(\\w+)', r'\\1 \\2', text)
    #print(text)
    text = re.sub(' (\\d+)([A-zА-яЁёӣҳқҷӯғӢҲҚҶӮҒīūėĪŪĖ]+) ', r' \\1 \\2 ', text)
    #print(text)
    text = re.sub(' ([A-zА-яЁёӣҳқҷӯғӢҲҚҶӮҒīūėĪŪĖ]+)(\\d+) ', r' \\1 \\2 ', text)
   # print(text)
    text = re.sub(' +', ' ', text)
    tokens = text.split(' ')
    newtokens = []
    for token in tokens:
        if len(token) >1 and any(t.isalpha() for t in token):
            if re.search('[№A-zА-яЁёӣҳқҷӯғӢҲҚҶӮҒīūėĪŪĖ0-9-]', token):
                newtokens.append(token)
            else:
                newtokens.append(token)
    return ' '.join(newtokens)

def specific_papers(text):
    cleaned = re.sub('#gallery.+} ', '', text, flags=re.M|re.S)
    cleaned = re.sub('#tdi_2_ffe.+?}', '', cleaned, flags=re.M | re.S)
    cleaned = re.sub('di_2.+?}', '', cleaned, flags=re.M | re.S)
    cleaned = re.sub('^ДУШАНБЕ, ? +?[0-9\.] ', '', cleaned)
    cleaned = re.sub('var.+?;', '', cleaned, flags=re.M | re.S)
    cleaned = re.sub('if ?\(.+?}\);', '', cleaned, flags=re.M | re.S)
    cleaned = re.sub('{.+?}', '', cleaned, flags=re.M | re.S)
    cleaned = re.sub('GLOBAL.+', '', cleaned)
    cleaned = re.sub('window\..+?;', '', cleaned, flags=re.M | re.S)
    cleaned = re.sub('<[A-z]+ class=.+', '', cleaned, flags=re.M | re.S)
    cleaned = re.sub('([\?\!\.])(\w)', r'\1 \2', cleaned)
    if len(cleaned.split('Таҷдиди ахир:'))>1:
        cleaned = re.sub('Таҷдиди ахир:.+', '', cleaned, flags=re.M|re.S)
    cleaned = re.sub('Sputnik Ҳамаи ҳуқуқҳо ҳимоя шудаанд. 18\+', '', cleaned)
    cleaned = re.sub('ДУШАНБЕ,.+ ?[—|-] ?Sputnik\.? ?', '\n', cleaned)
    cleaned = re.sub('©\n +Фото :.+?$', '', cleaned, flags=re.M|re.S)
    cleaned = re.sub('Огаҳирасонии Sputnik|Иштироки дарёфти огаҳиҳои Sputnik|}|\t|\xa0', '', cleaned)
    cleaned = re.sub('\n +|\n\n+', '\n', cleaned)
    cleaned = re.sub('Шоҳиди ҳодисае.+', '', cleaned)
    cleaned = re.sub('Лутфан, хабари.+', '', cleaned, flags=re.M|re.S)
    return cleaned

def clean_all(text):
    cleaned = specific_papers(text)
    cleaned = basic_subs(cleaned)
    cleaned = subs(cleaned)
    cleaned = re.sub('ДУШАНБЕ[^\.]+АМИТ[^\.]+«Ховар»[^\.]\. ?', '', cleaned)
    cleaned = re.sub('[^\.]+Sputnik[^\.]\. ?', '', cleaned)
    return cleaned
