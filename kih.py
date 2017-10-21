import pycurl
import sqlite3
from datetime import timedelta, date

db = sqlite3.connect("kih.db")
db.execute("CREATE TABLE IF NOT EXISTS episodes (date, pubdate, len integer);")

URL = "http://78.140.251.40/tmp_audio/itunes2/hik_-_rr_%s.mp3"
DATEFMT = "%Y-%m-%d"

def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield start_date + timedelta(n)

class Episode:
    exists = None
    pubdate = None

    def feed(self, header):
        header = header.rstrip()

        if b"200 OK" in header:
            self.exists = True
            return

        elif b"404 Not Found" in header:
            self.exists = False
            return

        if self.exists and b":" in header:
            k, v = map(bytes.strip, header.split(b":", 1))
            if k == b'Content-Length':
                self.length = int(v)
            elif k == b'Last-Modified':
                self.pubdate = v

def get_episode(date):
    result = Episode()
    c = pycurl.Curl()
    c.setopt(c.URL, URL % date.strftime(DATEFMT))
    c.setopt(c.HEADERFUNCTION, result.feed)
    c.setopt(c.NOBODY, True)
    c.perform()
    c.close()
    return result

def fetch():
    start_date = date(2016, 3, 14)
    end_date = date.today()
    for current in daterange(start_date, end_date):
        episode = get_episode(current)
        if episode.exists:
            print("%s: exists!" % current)
            db.execute("INSERT INTO episodes (date, pubdate, len) VALUES (?, ?, ?);",
                       (current.strftime(DATEFMT), episode.pubdate, episode.length))

db.commit()
db.close()
