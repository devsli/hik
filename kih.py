import pycurl
import sqlite3
from datetime import timedelta, date
from sys import argv

db = sqlite3.connect("kih.sqlite")
db.execute("""CREATE TABLE IF NOT EXISTS episodes
              (date PRIMARY KEY, pubdate, len integer);""")

URL = "http://78.140.251.40/tmp_audio/itunes2/hik_-_rr_%s.mp3"
FEED = "http://www.radiorecord.ru/rss.xml"
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
            db.execute("""INSERT INTO episodes (date, pubdate, len)
                          VALUES (?, ?, ?);""",
                       (current.strftime(DATEFMT), episode.pubdate,
                        episode.length))

def urls():
    for row in db.execute('SELECT date FROM episodes ORDER BY date'):
        print(URL % row[0])

def print_usage():
    print("Usage: %s fetch | urls" % argv[0])

if len(argv) == 1:
    print_usage()
else:
    if argv[1] == "fetch":
        fetch()
    elif argv[1] == "urls":
        urls()

db.commit()
db.close()
