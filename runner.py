import sqlite3
import datetime
import urllib.error
import time
import anime365
import all_translations
from requests.exceptions import ConnectionError, SSLError


while True:
    try:
        con = sqlite3.connect('anime365.db')
        # all_translations.run(con)
        # if int(datetime.datetime.now().strftime('%M')) % 5 == 0:
        anime365.run(con)
        con.close()
        print('ok')
        print(datetime.datetime.now())
        print('_______________________')
        time.sleep(1)
    except (urllib.error.HTTPError, ConnectionError, SSLError):
        print('Connection Error')
    except Exception:
        print('Exception')
        continue
