import sqlite3
import time
import random
import urllib.error
import anime365
import all_translations


while True:
    try:
        con = sqlite3.connect('anime365.db')
        anime365.run(con)
        all_translations.run(con)
        con.close()
        print('ok')
        print(random.random())
        time.sleep(1)
    except urllib.error.HTTPError:
        print('500!!!!!!!!!')
    except Exception:
        continue
