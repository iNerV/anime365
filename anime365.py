import urllib.request
import urllib.parse
import urllib
import json
import time
import requests
from settings import token, nickname


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

    if quality_type == 'tv':
        quality_type = 'tv'
    elif quality_type == 'bd':
        quality_type = 'bd'
    elif quality_type == 'dvd':
        quality_type = 'dvd'
    else:
        quality_type = 'unknown'

    c = conn.cursor()
    link = 'http://shikimori.org/api/animes/{id}/anime_videos'
    req = link.format(id=anime_id)
    # req = 'http://httpbin.org/post'
    anime_video = {'anime_id': int(anime_id),
                   "state": "uploaded",
                   'author_name': str(author_name),
                   'episode': int(episode),
                   'kind': str(kind),
                   'language': str(language),
                   'source': str(source),
                   'url': str(url),
                   'quality': str(quality_type)}
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
