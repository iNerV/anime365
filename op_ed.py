import requests
import sqlite3
import json
from settings import token, nickname

HEADERS = {'X-User-Nickname': nickname,
           'X-User-Api-Access-Token': token,
           'content-type': 'application/json'}


def get_video(conn):
    c = conn.cursor()
    f = open('op_ed.txt')
    for x in f:
        c.execute('INSERT INTO op_ed (anime_id, \
                                      video_id, \
                                      kind) \
                          VALUES (?, ?, ?)',
                  (x.rstrip().split('\t')[0],
                   x.rstrip().split('\t')[1],
                   x.rstrip().split('\t')[2]))
        conn.commit()
        print(x.rstrip().split('\t'))


def get_url_title(conn):
    link = 'https://smotret-anime.ru/api/translations/'
    c = conn.cursor()
    c.execute("SELECT anime_id, video_id, kind FROM op_ed WHERE uploaded=0")
    db = c.fetchall()
    for x in db:
        resp = requests.get(link+str(x[1])).json()
        try:
            c.execute('UPDATE op_ed SET url=?, title=?, uploaded=1 WHERE video_id=?', (
                str(resp['data']['url']),
                str(resp['data']['title']),
                x[1]))
            conn.commit()
            print(resp['data']['title'])
        except KeyError:
            c.execute('DELETE FROM op_ed WHERE video_id=?', (x[1],))


def del_unnecessary(conn):
    link = 'https://smotret-anime.ru/api/translations/'
    c = conn.cursor()
    c.execute("SELECT video_id FROM op_ed WHERE uploaded=1")
    db = c.fetchall()
    for x in db:
        try:
            print(x[0])
            resp = requests.get(link+str(x[0])).json()
            if int(float(resp['data']['episode']['episodeInt'])) > 2:
                print('del' + str(x[0]))
                c.execute('DELETE FROM op_ed WHERE video_id=?', (x[0],))
            else:
                print('ok')
                c.execute('UPDATE op_ed SET uploaded=? WHERE video_id=?', (0, x[0]))
                conn.commit()
        except TypeError:
                print('ok')
                c.execute('UPDATE op_ed SET uploaded=? WHERE video_id=?', (0, x[0]))
                conn.commit()


def post_video(conn):
    link = 'http://shikimori.org/api/animes/{id}/videos'
    c = conn.cursor()
    c.execute("SELECT anime_id, kind, url, title FROM op_ed WHERE uploaded=0")
    db = c.fetchone()
    req = link.format(id=db[0])
    anime_video = {
                    "url": db[2],
                    "kind": db[1],
                    "name": db[3]
                  }
    data = {'video': anime_video}
    param = requests.post(req, json=data, headers=HEADERS)
    c.execute('UPDATE op_ed SET uploaded=? WHERE anime_id=?', (1, db[0]))
    conn.commit()
    print(db)
    print(param.text)


def del_unactive(conn):
    c = conn.cursor()
    c.execute("SELECT video_id FROM op_ed WHERE uploaded=0")
    db = c.fetchall()
    for x in db:
        print(x[0])
        resp = requests.get('https://smotret-anime.ru/api/translations/{video_id}'.format(video_id=x[0])).json()
        if resp['data']['isActive'] != 1:
            print('del')
            c.execute("DELETE FROM op_ed WHERE video_id=?", (x[0],))
        else:
            print('ok')
            c.execute('UPDATE op_ed SET uploaded=? WHERE video_id=?', (1, x[0]))
            conn.commit()


if __name__ == '__main__':
    con = sqlite3.connect('anime365.db')
    post_video(con)
