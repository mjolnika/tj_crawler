import os, re


with open(f'metadata_{direct.replace("./", "")}.txt', encoding = 'utf-8') as f:
    lines = f.read().splitlines()
c = 0
new = []
lines = sorted(lines)
doubles = []
check_l = []
for line in lines:
    parts = line.split('\t')
    filename = f'{paper}_'+parts[0]
    source = parts[7]
    title = parts[2]
    year = parts[4]
    genre = 'газета'
    author = parts[1]
    title = re.sub('""', '⚘', title).strip(' "')
    title = re.sub('ВИДЕО ', '', title).replace('⚘', '"')
    long_title = f'{title}. {source}, {year}'
    if author and len(author.split(' '))<3:
        long_source = f'{source} ({author})'
    else:
        long_source = f'{source} ({source})'
    mark = 'с'
    long_author = ''
    century = '21'
    new_parts = [filename, source, title, long_title, genre, long_source, mark, century, long_author, year, year]
    check = '\t'.join(new_parts[1:])
    new_st = '\t'.join(new_parts)
    if check in check_l:
        print(new_parts[0])
        doubles.append(new_parts[0])
        try:
            c += 1
            os.remove(f'{direct}/{new_parts[0]}.txt')
            print('removed', c, new_parts[0])
        except FileNotFoundError:
            pass
    else:
        new.append(new_st)
        check_l.append('\t'.join(new_parts[1:]))



with open(f'metadataforcorpus{paper}.txt', 'w', encoding='utf-8') as f:
   f.write('\n'.join(new))