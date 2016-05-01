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


def add_to_db(translations, conn):
    c = conn.cursor()
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


def get_recent_translations(conn):
    print('get_recent_translations')
    c = conn.cursor()
    allow_type = ['tv', 'ova', 'ona', 'movie', 'special']
    headers = {'X-User-Nickname': nickname,
               'X-User-Api-Access-Token': token,
               'content-type': 'application/json'}
    for translations in get_recent_translations_json():
        c.execute("SELECT * \
                  FROM recent_translations \
                  WHERE (anime365_id LIKE ?)", (translations['id'],))
        db = c.fetchall()
        if len(db) > 0:
            pass
        else:
            time.sleep(1)
            print('test')
            req = 'https://shikimori.org/api/animes/{anime_id}'.format(anime_id=translations['series']['myAnimeListId'])
            response = requests.get(req, headers=headers).json()
            # print(translations['id'])
            # print(int(float(translations['episode']['episodeInt'])))
            if response.get('code', 200) == 404:
                print('error 404')
                continue
            elif translations['isActive'] == -1:
                print('isActive -1')
            elif translations['isActive'] == 0:
                print('isActive 0')
            elif translations['isActive'] == '0':
                print('isActive 0')
            elif translations['episode']['episodeInt'] == '':
                print('episode')
            elif translations['episode']['episodeInt'] == '0':
                print('episode #0')
            elif float(translations['episode']['episodeInt']) / int(float(translations['episode']['episodeInt'])) != 1:
                print('дробный эпизод')
            elif translations['series']['myAnimeListId'] == 0:
                print('MAL id')
            elif translations['typeKind'] == '':
                print('Typekind')
            elif translations['typeLang'] == '':
                print('typelang')
            elif translations['episode']['episodeType'] not in allow_type:
                print('allow_type')
            elif response['anons']:
                print('anons')
            elif response['episodes'] != 0 and response['episodes'] < int(float(translations['episode']['episodeInt'])):
                print('episodes')
                print(response['episodes'], int(float(translations['episode']['episodeInt'])))
            elif response['episodes_aired'] + 4 < int(translations['episode']['episodeInt']) \
                    and response['episodes_aired'] != 0:
                print('episodes_aired')
                print(response['episodes_aired'], int(translations['episode']['episodeInt']))
                print(translations['series']['myAnimeListId'])
            elif response['kind'] != translations['episode']['episodeType']:
                print('kind')
            else:
                if translations['duration'] != '0' and response['duration'] != 0:
                    if float(translations['duration']) < (
                                (response['duration'] * 60) - ((response['duration'] * 60) / 3)):
                        print('duration')
                    else:
                        add_to_db(translations, conn)
                else:
                    add_to_db(translations, conn)


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
                   'quality': str(quality_type)}
    data = {'anime_video': anime_video}
    headers = {'X-User-Nickname': nickname,
               'X-User-Api-Access-Token': token,
               'content-type': 'application/json'}
    param = requests.post(req, data=json.dumps(data), headers=headers)
    c.execute('UPDATE recent_translations \
        SET uploaded=? WHERE url=?', (1, url))
    conn.commit()
    print(param.text)
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
