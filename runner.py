import sqlite3
import datetime
import urllib.error
import time
import anime365
# import delete_broken
# import all_translations
import op_ed
from requests.exceptions import ConnectionError, SSLError


while True:
    try:
        con = sqlite3.connect('anime365.db')
        # all_translations.run(con)
        # if int(datetime.datetime.now().strftime('%M')) % 5 == 0:
        anime365.run(con)
        # op_ed.post_video(con)
        # delete_broken.delete_video(con)
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
