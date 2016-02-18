import urllib.request
import urllib.parse
import urllib
import urllib.error
import json
import time
import requests
from settings import token, nickname


def get_all_translations_json(offset):  # получить ВСЕ переводы
    print('get_all_translations_json')
    print(offset)
    req = "http://smotret-anime.ru/api/translations/?"
    data = urllib.parse.urlencode({
        'limit': 1,
        'offset': offset,
        'pretty': '1'})
    binary_data = data.encode('utf8')
    req2 = urllib.request.Request(req)
    param = urllib.request.urlopen(req2, binary_data)
    return json.loads(param.read().decode())


def get_all_translations(conn, offset):  # получить ВСЕ переводы
    print('get_all_translations')
    print(offset)
    c = conn.cursor()
    try:
        if get_all_translations_json(offset)['error']['code'] == 404:
            print('ATAS!')
            get_all_translations(conn, offset + 1)
    except KeyError:
        translations = get_all_translations_json(offset)['data'][0]
        c.execute("SELECT * \
                  FROM all_translations \
                  WHERE (anime365_id LIKE ?)", (translations['id'],))
        db = c.fetchall()
        if len(db) > 0:
            print('Есть в базе!')
            get_all_translations(conn, offset + 1)
        else:
            try:
                print('TEST!')
                if translations['isActive'] == -1:
                    print('isActive -1')
                    get_all_translations(conn, offset + 1)
                elif translations['isActive'] == 0:
                    print('isActive 0')
                    get_all_translations(conn, offset + 1)
                elif translations['isActive'] == '0':
                    get_all_translations(conn, offset + 1)
                elif translations['episode']['episodeInt'] == '':
                    print('episode')
                    get_all_translations(conn, offset + 1)
                elif float(translations['episode']['episodeInt']) / int(translations['episode']['episodeInt']) != 1:
                    print('AAAAAAAAAAA')
                    get_all_translations(conn, offset + 1)
                elif translations['series']['myAnimeListId'] == 0:
                    print('MAL id')
                    get_all_translations(conn, offset + 1)
                elif translations['typeKind'] == '':
                    print('Typekind')
                    get_all_translations(conn, offset + 1)
                elif translations['typeLang'] == '':
                    print('typelang')
                    get_all_translations(conn, offset + 1)
                else:
                    c.execute('INSERT INTO all_translations (mal_id, \
                                  typeKind, \
                                  typeLang, \
                                  authorsSummary, \
                                  url, \
                                  episodeInt, \
                                  anime365_id, \
                                  uploaded, \
                                  qualityType, \
                                  offset) \
                                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                              (translations['series']['myAnimeListId'],
                               translations['typeKind'],
                               translations['typeLang'],
                               translations['authorsSummary'],
                               translations['url'],
                               translations['episode']['episodeInt'],
                               translations['id'],
                               0,
                               translations['qualityType'],
                               offset))
                    conn.commit()
            except (TypeError, ZeroDivisionError):
                print('TypeError, ZeroDivisionError')
                get_all_translations(conn, offset + 1)


def get_shiki_video(mal_id):
    print("get_shiki_video")
    req = 'http://shikimori.org/api/animes/{id}/anime_videos'.format(id=mal_id)
    headers = {'X-User-Nickname': nickname,
               'X-User-Api-Access-Token': token}
    req2 = urllib.request.Request(req, headers=headers)
    param = urllib.request.urlopen(req2)
    return json.loads(param.read().decode())


def get_video_url_shiki(mal_id):
    print('get_video_url_shiki')
    urls = []
    for url in get_shiki_video(mal_id):
        urls.append(url['url'])
    return urls


def compare_urls(anime365, mal_id):  # Выпилить нахер, все равно не нужна
    print('compare_urls')
    s = 'https://smotret-anime.ru/translations/embed/'
    if s+str(anime365) in get_video_url_shiki(mal_id):
        print('Compare FALSE')
        return True
    else:
        print('Compare TRUE')
        return True


def check_quality(qt):
    if qt == 'tv':
        return '(TV) '
    elif qt == 'bd':
        return '(BD) '
    elif qt == 'dvd':
        return '(DVD '
    else:
        return ''


def check_lang(lang, kind):
    print('lang')
    if lang == 'english' and kind == 'subtitles':
        return ' (Английские субтитры)'
    elif lang == 'japanese' and kind == 'subtitles':
        return ' (Японские субтитры)'
    else:
        return ''


def post_video_shiki(anime_id,
                     author_name,
                     episode,
                     kind,
                     language,
                     source,
                     url,
                     conn,
                     quality_type):
    print('post_video_shiki')
    if kind == 'sub':
        kind = 'subtitles'
    elif kind == 'raw':
        kind = 'raw'
    elif kind == 'voice':
        kind = 'fandub'
    elif kind == '':
        kind = 'unknown'

    if language == 'ru':
        language = 'russian'
    elif language == 'en':
        language = 'english'
    elif language == 'jp':
        language = 'japanese'
    elif language == '':
        language = 'unknown'

    c = conn.cursor()
    link = 'http://shikimori.org/api/animes/{id}/anime_videos'
    req = link.format(id=anime_id)
    # req = 'http://httpbin.org/post'
    anime_video = {'anime_id': int(anime_id),
                   "state": "uploaded",
                   'author_name': str(check_quality(quality_type) +
                                      author_name +
                                      check_lang(language, kind)),
                   'episode': int(episode),
                   'kind': str(kind),
                   'language': str(language),
                   'source': str(source),
                   'url': str(url)}
    data = {'anime_video': anime_video}
    headers = {'X-User-Nickname': nickname,
               'X-User-Api-Access-Token': token,
               'content-type': 'application/json'}
    param = requests.post(req, data=json.dumps(data), headers=headers)
    c.execute('UPDATE all_translations \
        SET uploaded=? WHERE url=?', (1, url))
    conn.commit()
    print(param.text)
    return param.text


def prepare_video_shiki(conn):
    print('prepare_video_shiki')
    c = conn.cursor()
    db = []
    c.execute("SELECT * FROM all_translations \
              WHERE (uploaded \
              LIKE {upl})".format(upl=0))
    for dbd in c.fetchall():
        db.append(dbd)
    for x in db:
        if compare_urls(x[6], x[0]):
            post_video_shiki(x[0],
                             x[3],
                             x[5],
                             x[1],
                             x[2],
                             x[4],
                             x[4],
                             conn,
                             x[8])
        time.sleep(1)
    return db


def get_last_entry(conn):
    c = conn.cursor()
    c.execute('SELECT offset \
              FROM all_translations \
              WHERE offset IN (SELECT MAX(offset) \
                                    FROM all_translations)')
    return c.fetchone()[0]


def run(conn):
    prepare_video_shiki(conn)
    get_all_translations(conn, get_last_entry(conn) + 1)
