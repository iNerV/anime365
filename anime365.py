import urllib.request
import urllib.parse
import urllib
import json
import time
import requests
from settings import token, password, nickname


def get_token():
    # req = "http://shikimori.org/api/access_token"
    req = 'http://httpbin.org/post'
    data = urllib.parse.urlencode({
        'nickname': nickname,
        'password': password})
    binary_data = data.encode('utf8')
    req2 = urllib.request.Request(req, binary_data)
    param = urllib.request.urlopen(req2)
    return json.loads(param.read().decode())


def get_recent_translations_json():
    print('get_recent_translations_json')
    req = "http://smotret-anime.ru/api/translations/?"
    data = urllib.parse.urlencode({
        'feed': 'recent',
        'pretty': '1'})
    binary_data = data.encode('utf8')
    req2 = urllib.request.Request(req)
    param = urllib.request.urlopen(req2, binary_data)
    return json.loads(param.read().decode())['data']


def get_recent_translations(conn):
    print('get_recent_translations')
    c = conn.cursor()
    for translations in get_recent_translations_json():
        c.execute("SELECT * \
                  FROM recent_translations \
                  WHERE (anime365_id LIKE ?)", (translations['id'],))
        db = c.fetchall()
        if len(db) > 0:
            pass
        else:
            c.execute('INSERT INTO recent_translations (mal_id, \
                      typeKind, \
                      typeLang,\
                      authorsSummary,\
                      url,\
                      episodeInt, \
                      anime365_id, \
                      uploaded, \
                      qualityType) \
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                      (translations['series']['myAnimeListId'],
                       translations['typeKind'],
                       translations['typeLang'],
                       translations['authorsSummary'],
                       translations['url'],
                       translations['episode']['episodeInt'],
                       translations['id'],
                       0,
                       translations['qualityType']))
            conn.commit()


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
    c.execute('UPDATE recent_translations \
        SET uploaded=? WHERE url=?', (1, url))
    conn.commit()
    return param.text


def prepare_video_shiki(conn):
    print('prepare_video_shiki')
    c = conn.cursor()
    db = []
    c.execute("SELECT * FROM recent_translations \
              WHERE (uploaded \
              LIKE {upl})".format(upl=0))
    for dbd in c.fetchall():
        db.append(dbd)
    for x in db:
        post_video_shiki(x[1],
                         x[4],
                         x[6],
                         x[2],
                         x[3],
                         x[5],
                         x[5],
                         conn,
                         x[9])
        time.sleep(1)
    return db


def run(conn):
        get_recent_translations(conn)
        prepare_video_shiki(conn)
