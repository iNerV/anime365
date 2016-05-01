import requests
import sqlite3
import time
import datetime
from requests.exceptions import SSLError, ConnectionError
from json.decoder import JSONDecodeError
from settings import token, nickname


def get_all_my_video(conn, pg):
    c = conn.cursor()
    req = 'http://shikimori.org/api/users/4193/anime_video_reports?limit=500&page={pg}'.format(pg=pg)
    headers = {'X-User-Nickname': nickname,
               'X-User-Api-Access-Token': token,
               'content-type': 'application/json'}
    response = requests.get(req, headers=headers).json()
    for x in response:
        c.execute('INSERT INTO all_my_videos (anime_id, \
                   video_id, \
                   url) \
                   VALUES (?, ?, ?)',
                  (x['anime_video']['anime_id'],
                   x['anime_video']['id'],
                   x['anime_video']['url']))
        conn.commit()


def get_all_anime(conn):
    c = conn.cursor()
    anime = []
    c.execute("SELECT anime_id FROM all_my_videos",)
    db = c.fetchall()
    for x in db:
        anime.append(x[0])
    for x in set(anime):
        c.execute('INSERT INTO all_anime(anime_id) VALUES (?)', (x,))
    conn.commit()
    return set(anime)


def get_duration(conn):
    c = conn.cursor()
    headers = {'X-User-Nickname': nickname,
               'X-User-Api-Access-Token': token,
               'content-type': 'application/json'}
    c.execute("SELECT anime_id FROM all_anime",)
    db = c.fetchall()
    for x in db:
        req = 'https://shikimori.org/api/animes/{anime_id}'.format(anime_id=x[0])
        response = requests.get(req, headers=headers).json()
        c.execute('UPDATE all_my_videos SET ep_duration=? WHERE anime_id=?', (response['duration'], x[0]))
        print(x[0])
        conn.commit()
        c.execute('DELETE FROM all_anime WHERE anime_id=?', (x[0],))
        time.sleep(0.7)


def delete_video(conn):
    c = conn.cursor()
    headers = {'X-User-Nickname': nickname,
               'X-User-Api-Access-Token': token,
               'content-type': 'application/json'}
    c.execute("SELECT url, anime_id, video_id, ep_duration FROM all_my_videos WHERE check_anime='FALSE'")
    db = c.fetchall()
    for x in db:
        try:
            req = x[0].replace('smotret-anime.ru/translations/embed/', 'smotret-anime.ru/api/translations/')
            resp = requests.get(req).json()
            r = 'ok'
            allow_type = ['tv', 'ova', 'ona', 'movie', 'special']
            if 'error' in resp:
                time.sleep(0.7)
                r = requests.delete('https://shikimori.org/api/animes/{anime_id}/anime_videos/{video_id}'
                                    .format(anime_id=x[1], video_id=x[2]), headers=headers).text
                c.execute('INSERT INTO delete_broken (anime_id, \
                                                      video_id, \
                                                      url) \
                          VALUES (?, ?, ?)',
                          (x[1],
                           x[2],
                           x[0]))
            elif resp['data']['episode'] is None:
                time.sleep(0.7)
                r = requests.delete('https://shikimori.org/api/animes/{anime_id}/anime_videos/{video_id}'
                                    .format(anime_id=x[1], video_id=x[2]), headers=headers).text
                c.execute('INSERT INTO delete_broken (anime_id, \
                                                      video_id, \
                                                      url) \
                          VALUES (?, ?, ?)',
                          (x[1],
                           x[2],
                           x[0]))

            elif resp['data']['episode']['episodeType'] not in allow_type:
                time.sleep(0.7)
                r = requests.delete('https://shikimori.org/api/animes/{anime_id}/anime_videos/{video_id}'
                                    .format(anime_id=x[1], video_id=x[2]), headers=headers).text
                c.execute('INSERT INTO delete_broken (anime_id, \
                                                      video_id, \
                                                      url) \
                          VALUES (?, ?, ?)',
                          (x[1],
                           x[2],
                           x[0]))
            elif resp['data']['duration'] != '0' and x[3] != 0:
                if float(resp['data']['duration']) < ((x[3]*60)-((x[3]*60)/3)):
                    time.sleep(0.7)
                    r = requests.delete('https://shikimori.org/api/animes/{anime_id}/anime_videos/{video_id}'
                                        .format(anime_id=x[1], video_id=x[2]), headers=headers).text
                    c.execute('INSERT INTO delete_broken (anime_id, \
                                                          video_id, \
                                                          url) \
                              VALUES (?, ?, ?)',
                              (x[1],
                               x[2],
                               x[0]))
            elif resp['data']['isActive'] != 1:
                time.sleep(0.7)
                r = requests.delete('https://shikimori.org/api/animes/{anime_id}/anime_videos/{video_id}'
                                    .format(anime_id=x[1], video_id=x[2]), headers=headers).text
                c.execute('INSERT INTO delete_broken (anime_id, \
                                                      video_id, \
                                                      url) \
                          VALUES (?, ?, ?)',
                          (x[1],
                           x[2],
                           x[0]))
            c.execute("UPDATE all_my_videos SET check_anime='TRUE' WHERE video_id=?", (x[2],))
            conn.commit()
            print(r, datetime.datetime.now())
        except (SSLError, ConnectionError, JSONDecodeError):
            delete_video(conn)


def run():
    con = sqlite3.connect('anime365.db')
    delete_video(con)

run()
