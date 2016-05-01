import urllib.request
import urllib.parse
import urllib
import urllib.error
import json
import time
import requests
from settings import token, nickname


def get_all_translations_json(after_id):  # получить ВСЕ переводы
    print('get_all_translations_json')
    print(after_id)
    req = "https://smotret-anime.ru/api/translations/?"
    data = urllib.parse.urlencode({
        'limit': 1,
        'offset': 1,
        'pretty': 1,
        'feed': 'id',
        'afterId': after_id})
    binary_data = data.encode('utf8')
    req2 = urllib.request.Request(req)
    param = urllib.request.urlopen(req2, binary_data)
    print(json.loads(param.read().decode()))
    return json.loads(param.read().decode())


def add_to_db(translations, offset, conn):
    c = conn.cursor()
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


def get_all_translations(conn, offset):  # получить ВСЕ переводы
    print('get_all_translations')
    allow_type = ['tv', 'ova', 'ona', 'movie', 'special']
    headers = {'X-User-Nickname': nickname,
               'X-User-Api-Access-Token': token,
               'content-type': 'application/json'}
    js_resp = get_all_translations_json(offset)
    c = conn.cursor()
    try:
        if js_resp['error']['code'] == 404:
            print('ATAS!')
            get_all_translations(conn, offset + 1)
    except KeyError:
        print(js_resp)
        translations = js_resp['data'][0]
        c.execute("SELECT * \
                  FROM all_translations \
                  WHERE (anime365_id LIKE ?)", (translations['id'],))
        db = c.fetchall()
        if len(db) > 0:
            print('Есть в базе!')
            get_all_translations(conn, offset + 1)
        else:
            try:
                print(offset)
                time.sleep(1)
                req = 'https://shikimori.org/api/animes/{anime_id}'.format(
                    anime_id=translations['series']['myAnimeListId'])
                response = requests.get(req, headers=headers).json()
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
                elif translations['episode']['episodeInt'] == '0':
                    print('episode #0')
                    get_all_translations(conn, offset + 1)
                elif float(translations['episode']['episodeInt']) / int(
                        float(translations['episode']['episodeInt'])) != 1:
                    print('Дробный эпизод')
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
                elif translations['episode']['episodeType'] not in allow_type:
                    print('allow_type')
                    get_all_translations(conn, offset + 1)
                elif response['anons']:
                    print('anons')
                    get_all_translations(conn, offset + 1)
                elif response['episodes'] != 0 and response['episodes'] < int(
                        float(translations['episode']['episodeInt'])):
                    print('episodes')
                    get_all_translations(conn, offset + 1)
                elif response['episodes_aired'] + 4 < int(float(translations['episode']['episodeInt'])):
                    print('episodes_aired')
                    get_all_translations(conn, offset + 1)
                elif response['kind'] != translations['episode']['episodeType']:
                    print('kind')
                    get_all_translations(conn, offset + 1)
                else:
                    print('Финальная проверка')
                    if translations['duration'] != '0' and response['duration'] != 0:
                        print('pre-last test')
                        if float(translations['duration']) < (
                                    (response['duration'] * 60) - ((response['duration'] * 60) / 3)):
                            print('duration')
                            get_all_translations(conn, offset + 1)
                        else:
                            print('last test')
                            add_to_db(translations, offset, conn)
                    else:
                        print('last call')
                        add_to_db(translations, offset, conn)
            except (TypeError, ZeroDivisionError, ValueError, KeyError):
                print('TypeError, ZeroDivisionError, ValueError, KeyError')
                get_all_translations(conn, offset + 1)


def check_quality(qt):
    print('check_quality')
    if qt == 'tv':
        return 'tv'
    elif qt == 'bd':
        return 'bd'
    elif qt == 'dvd':
        return 'dvd'
    else:
        return 'unknown'


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
        language = 'original'
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
                   'quality': str(check_quality(quality_type))}
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
