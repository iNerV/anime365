import sqlite3
import time
import datetime
import requests
from settings import token, nickname

"""
class Validator:
    # ALLOW_TYPE = ['tv', 'ova', 'ona', 'movie', 'special']
    ALLOW_TYPE_OP_ED = ['ending', 'opening', 'preview']

    def __init__(self, anime_info, video_info, allow_type=None):
        if allow_type is None:
            self.ALLOW_TYPE = ['tv', 'ova', 'ona', 'movie', 'special']
        else:
            self.ALLOW_TYPE = allow_type
        self.ALLOW_TYPE = allow_type

        self.anime_info = anime_info
        self.video_info = video_info

        self.validators = [self._is_aired_episode(), self._check_duration(), self._is_allow_type(),
                           self._is_active(), self._has_kind(), self._has_lang(), self._check_number_of_episode()]

    def validate(self) -> bool:
        print('_validate')
        if self._has_mal_id():
            if self._is_404() or self._is_anons():  # fixme op/ed/pv не пройдут
                return False
            if all(self.validators):
                return True
        return False

    def _is_404(self) -> bool:
        print('_is_404')
        if self.anime_info.get('code', 200) == 404:
            return True
        return False

    def _is_anons(self) -> bool:
        print('_is_anons')
        if self.anime_anons:
            return True
        return False

    def _is_aired_episode(self) -> bool:
        print('_is_aired_episode')
        if self.episodes_aired + 2 < int(float(self.episode)) and self.episodes_aired != 0:
            return False
        return True

    def _check_duration(self) -> bool:
        print('_check_duration')
        if self.episode_duration != '0' and self.episode_duration != 0:
            duration_in_minutes = self.anime_duration * 60
            if float(self.episode_duration) < (duration_in_minutes - (duration_in_minutes / 3)):
                return False
            else:
                return True
        return False

    def _is_allow_type(self) -> bool:
        print('_is_allow_type')
        if self.episode_type not in self.ALLOW_TYPE:
            return False
        return True

    def _is_active(self) -> bool:
        print('_is_active')
        if self.episode_active != 1:
            return False
        return True

    def _has_mal_id(self) -> bool:
        print('_has_mal_id')
        if self.episode_mal_id == 0:
            return False
        return True

    def _has_kind(self) -> bool:
        print('_has_kind')
        if self.episode_kind == '':
            return False
        return True

    def _check_kind(self) -> bool:
        print('_check_kind')
        if self.anime_kind != self.episode_type:
            return False
        return True

    def _has_lang(self) -> bool:
        print('_has_lang')
        if self.episode_lang == '':
            return False
        return True

    def _check_number_of_episode(self) -> bool:
        print('_check_number_of_episode')
        if self.episode == '' or self.episode == '0':
            return False
        elif float(self.episode) / int(float(self.episode)) != 1:
            return False
        return True


class Anime:
    def __init__(self, anime_info):
        self.anime_info = anime_info

    @property
    def get_kind(self) -> str:
        return self.anime_info['kind']

    @property
    def get_duration(self) -> str:
        return self.anime_info['duration']

    @property
    def is_anons(self) -> bool:
        return self.anime_info['anons']

    @property
    def is_aired(self) -> bool:
        return self.anime_info['episodes_aired']


class Episode:
    def __init__(self, video_info):
        self.video_info = video_info
        self.kind = self.video_info['typeKind']
        self.lang = self.video_info['typeLang']
        self.quality = self.video_info['qualityType']
        self.type = self.video_info['episode']['episodeType']

    @property
    def get_id(self):
        return self.video_info['id']

    @property
    def get_quality(self):
        return self.quality

    @property
    def get_author(self):
        return self.video_info['authorsSummary']

    @property
    def get_url(self):
        return self.video_info['embedUrl']

    @property
    def get_number(self):
        return self.video_info['episode']['episodeInt']

    @property
    def get_duration(self):
        return self.video_info['duration']

    @property
    def get_type(self):
        return self.type

    @property
    def get_kind(self):
        return self.kind

    @property
    def get_lang(self):
        return self.lang

    @property
    def get_mal_id(self):
        return self.video_info['series']['myAnimeListId']

    @property
    def is_active(self):
        return self.video_info['isActive']

    def set_lang(self, new_lang):
        self.lang = new_lang

    def set_kind(self, new_kind):
        self.kind = new_kind

    def set_type(self, new_type):
        self.type = new_type

    def set_quality(self, new_quality):
        self.quality = new_quality
"""

class Bot(object):
    ALLOW_TYPE = ['tv', 'ova', 'ona', 'movie', 'special']
    ALLOW_TYPE_OP_ED = ['ending', 'opening', 'preview']
    SMORET_ANIME_API_URL = "https://smotret-anime.ru/api/translations/?"
    USER_AGENT = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.0; WOW64; rv:24.0) Gecko/20100101 Firefox/24.0'}
    HEADERS = {'X-User-Nickname': nickname,
               'X-User-Api-Access-Token': token,
               'content-type': 'application/json'}

    def __init__(self):
        self.conn = sqlite3.connect('anime365.db')

    def __del__(self):
        self.conn.close()

    def _fetch_updates_from_smotret_anime(self):
        print('_fetch_updates_from_smotret_anime')
        payload = {
            'feed': 'updatedDateTime',
            # 'pretty': '1',
            # 'limit': '1000'
        }
        r = requests.get(self.SMORET_ANIME_API_URL, params=payload, headers=self.USER_AGENT).json()
        return r['data']

    def check_changes(self):
        print('check_changes')
        c = self.conn.cursor()
        for x in self._fetch_updates_from_smotret_anime():
            c.execute("SELECT * FROM recent_translations WHERE (anime365_id LIKE ?)", (x['id'],))
            db = c.fetchone()
            if db:
                if x['episode']['episodeType'] not in self.ALLOW_TYPE \
                        or int(x['episode']['episodeInt']) != db[6] \
                        or x['series']['myAnimeListId'] != db[1] or x['isActive'] != 1:
                    c.execute('INSERT INTO delete_broken (anime_id, video_id, url, deleted) VALUES (?, ?, ?, ?)',
                              (db[1],
                               db[11],
                               db[5],
                               0))
                    self.conn.commit()
                    c.execute("DELETE FROM recent_translations WHERE anime365_id=?", (x['id'],))
                    self.conn.commit()
                    if self._validate(x):
                        translation = self._before_add_to_db(x)
                        self._add_to_db(translation)
                    else:
                        translation = self._before_add_to_db(x)
                        self._add_to_db(translation, broken=1)

    def _add_op_ed_to_db(self, translation):
        print('_add_op_ed_to_db')
        c = self.conn.cursor()
        c.execute('INSERT INTO op_ed (anime_id, \
                                      video_id, \
                                      kind, \
                                      url, \
                                      title) \
                          VALUES (?, ?, ?, ?, ?)',
                  (translation['series']['myAnimeListId'],
                   translation['id'],
                   translation['episode']['episodeType'],
                   translation['url'],
                   translation['title']))
        self.conn.commit()

    def _add_to_db(self, translation, broken=0):
        print('_add_to_db')
        c = self.conn.cursor()
        c.execute('INSERT INTO recent_translations (mal_id, \
                                      typeKind, \
                                      typeLang,\
                                      authorsSummary,\
                                      url,\
                                      episodeInt, \
                                      anime365_id, \
                                      uploaded, \
                                      qualityType, \
                                      broken) \
                                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                  (translation['series']['myAnimeListId'],
                   translation['typeKind'],
                   translation['typeLang'],
                   translation['authorsSummary'],
                   translation['url'],
                   translation['episode']['episodeInt'],
                   translation['id'],
                   0,
                   translation['qualityType'],
                   broken))
        self.conn.commit()

    def _fetch_translations_from_smotret_anime(self):
        print('_fetch_translations_from_smotret_anime')
        payload = {
            'feed': 'recent',
            # 'pretty': '1',
            # 'limit': '1000'
        }
        r = requests.get(self.SMORET_ANIME_API_URL, params=payload, headers=self.USER_AGENT).json()
        return r['data']

    def _fetch_anime_info_from_shikimori(self, translation):
        print('_fetch_anime_info_from_shikimori')
        req = 'https://shikimori.org/api/animes/{anime_id}'.format(anime_id=translation['series']['myAnimeListId'])
        response = requests.get(req, headers=self.HEADERS).json()
        return response

    def get_translations(self):
        print('get_translations')
        c = self.conn.cursor()
        for translation in self._fetch_translations_from_smotret_anime():
            c.execute("SELECT * \
                      FROM recent_translations \
                      WHERE (anime365_id LIKE ?)", (translation['id'],))
            db = c.fetchall()
            if len(db) > 0:
                pass
            else:
                if self._validate(translation):
                    translation = self._before_add_to_db(translation)
                    self._add_to_db(translation)
                elif self._is_allow_type_for_op_ed(translation):
                    translation = self._before_add_to_db(translation)
                    self._add_op_ed_to_db(translation)
                else:
                    translation = self._before_add_to_db(translation)
                    self._add_to_db(translation, broken=1)

    def _validate(self, translation):
        print('_validate')
        if self._has_mal_id(translation):
            time.sleep(0.7)
            anime_info = self._fetch_anime_info_from_shikimori(translation)
            if self._is_404(anime_info) or self._is_anons(anime_info):
                return False
            if self._is_aired_episode(translation, anime_info) and \
                    self._check_duration(translation, anime_info) and \
                    self._is_allow_type(translation) and \
                    self._is_active(translation) and \
                    self._has_kind(translation) and \
                    self._has_lang(translation) and \
                    self._check_number_of_episode(translation):
                return True
        return False

    @staticmethod
    def _before_add_to_db(translation):
        print('_before_add_to_db')
        if translation['typeKind'] == 'sub':
            translation['typeKind'] = 'subtitles'
        elif translation['typeKind'] == 'raw':
            translation['typeKind'] = 'raw'
        elif translation['typeKind'] == 'voice':
            translation['typeKind'] = 'fandub'
        else:
            translation['typeKind'] = 'unknown'

        if translation['typeLang'] == 'ru':
            translation['typeLang'] = 'russian'
        elif translation['typeLang'] == 'en':
            translation['typeLang'] = 'english'
        elif translation['typeLang'] == 'jp':
            translation['typeLang'] = 'original'
        else:
            translation['typeLang'] = 'unknown'

        if translation['qualityType'] == 'tv':
            translation['qualityType'] = 'tv'
        elif translation['qualityType'] == 'bd':
            translation['qualityType'] = 'bd'
        elif translation['qualityType'] == 'dvd':
            translation['qualityType'] = 'dvd'
        else:
            translation['qualityType'] = 'unknown'

        if translation['episode']['episodeType'] == 'opening':
            translation['episode']['episodeType'] = 'op'
        elif translation['episode']['episodeType'] == 'ending':
            translation['episode']['episodeType'] = 'ed'
        elif translation['episode']['episodeType'] == 'preview':
            translation['episode']['episodeType'] = 'pv'
        else:
            translation['episode']['episodeType'] = 'other'

        return translation

    @staticmethod
    def _is_404(anime_info):
        print('_is_404')
        if anime_info.get('code', 200) == 404:
            return True
        return False

    @staticmethod
    def _is_anons(anime_info):
        print('_is_anons')
        if anime_info['anons']:
            return True
        return False

    @staticmethod
    def _is_aired_episode(translation, anime_info):
        print('_is_aired_episode')
        if anime_info['episodes_aired'] + 2 < int(translation['episode']['episodeInt']) \
                and anime_info['episodes_aired'] != 0:
            return False
        return True

    @staticmethod
    def _check_duration(translation, anime_info):
        print('_check_duration')
        if translation['duration'] != '0' and translation['duration'] != 0:
            duration_in_minutes = anime_info['duration'] * 60
            if float(translation['duration']) < (duration_in_minutes - (duration_in_minutes / 3)):
                return False
            else:
                return True
        return False

    def _is_allow_type(self, translation):
        print('_is_allow_type')
        if translation['episode']['episodeType'] not in self.ALLOW_TYPE:
            return False
        return True

    def _is_allow_type_for_op_ed(self, translation):
        print('_is_allow_type')
        if translation['episode']['episodeType'] not in self.ALLOW_TYPE_OP_ED:
            return False
        return True

    @staticmethod
    def _is_active(translation):
        print('_is_active')
        if translation['isActive'] != 1:
            return False
        return True

    @staticmethod
    def _has_mal_id(translation):
        print('_has_mal_id')
        if translation['series']['myAnimeListId'] == 0:
            return False
        return True

    @staticmethod
    def _has_kind(translation):
        print('_has_kind')
        if translation['typeKind'] == '':
            return False
        return True

    @staticmethod
    def _check_kind(translation, anime_info):
        print('_check_kind')
        if anime_info['kind'] != translation['episode']['episodeType']:
            return False
        return True

    @staticmethod
    def _has_lang(translation):
        print('_has_lang')
        if translation['typeLang'] == '':
            return False
        return True

    @staticmethod
    def _check_number_of_episode(translation):
        print('_check_number_of_episode')
        if translation['episode']['episodeInt'] == '':
            return False
        elif translation['episode']['episodeInt'] == '0':
            return False
        elif float(translation['episode']['episodeInt']) / int(float(translation['episode']['episodeInt'])) != 1:
            return False
        return True

    def post_op_ed_to_shikimori(self):
        print('post_op_ed_to_shikimori')
        link = 'http://shikimori.org/api/animes/{id}/videos'
        c = self.conn.cursor()
        c.execute("SELECT anime_id, kind, url, title FROM op_ed WHERE uploaded=0")
        db = c.fetchall()
        for x in db:
            time.sleep(0.7)
            req = link.format(id=x[0])
            anime_video = {
                "url": x[2],
                "kind": x[1],
                "name": x[3]
            }
            data = {'video': anime_video}
            param = requests.post(req, json=data, headers=self.HEADERS)
            print(param.json())
            c.execute('UPDATE op_ed SET uploaded=? WHERE anime_id=?', (1, x[0]))
            self.conn.commit()

    def _post_video_to_shikimori(self, anime_id, author_name, episode, kind, language, source, url, quality_type):
        print('_post_video_to_shikimori')
        c = self.conn.cursor()
        link = 'https://shikimori.org/api/animes/{id}/anime_videos'
        req = link.format(id=anime_id)
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
        r = requests.post(req, json=data, headers=self.HEADERS)
        print(r.json())
        if r.json().get('errors') == ['Url видео с такой ссылкой уже добавлено']:
            c.execute('UPDATE recent_translations \
                            SET uploaded=? WHERE url=?', (1, url))
            self.conn.commit()
        if r.json().get('id'):
            c.execute('UPDATE recent_translations \
                SET uploaded=?, video_id=? WHERE url=?', (1, r.json()['id'], url))
            self.conn.commit()

    def prepare_video_for_shikimori(self):
        print('prepare_video_for_shikimori')
        c = self.conn.cursor()
        db = []
        c.execute("SELECT * FROM recent_translations \
                  WHERE (uploaded LIKE {upl} AND broken LIKE {broken})".format(upl=0, broken=0))
        for x in c.fetchall():
            db.append(x)
        for x in db:
            time.sleep(0.7)
            self._post_video_to_shikimori(x[1], x[4], x[6], x[2], x[3], x[5], x[5], x[9])

    def delete_video_from_shikimori(self):
        print('delete_video_from_shikimori')
        c = self.conn.cursor()
        c.execute("SELECT anime_id, video_id FROM delete_broken WHERE deleted=0")
        db = c.fetchall()
        if len(db) > 0:
            for x in db:
                r = requests.delete('http://shikimori.org/api/animes/{anime_id}/anime_videos/{video_id}'
                                    .format(anime_id=x[0], video_id=x[1]), headers=self.HEADERS)
                print(r.text)
                print(x)
                c.execute('UPDATE delete_broken SET deleted = 1 WHERE video_id=?', (x[1],))
                self.conn.commit()
                time.sleep(0.7)

    def run(self):
        while True:
            self.get_translations()
            self.prepare_video_for_shikimori()
            self.check_changes()
            self.delete_video_from_shikimori()
            self.post_op_ed_to_shikimori()
            print('ok')
            print(datetime.datetime.now())
            print('_______________________')


if __name__ == '__main__':
    bot = Bot()
    bot.run()
