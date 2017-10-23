import pycurl
import sqlite3
import feedparser
from datetime import timedelta, date
from sys import argv
from jinja2 import Environment, PackageLoader, select_autoescape
from codecs import decode
import eyed3

db = sqlite3.connect("kih.sqlite")
db.execute("""CREATE TABLE IF NOT EXISTS episodes
              (pubdate,
               len integer,
               title,
               itunes_author,
               itunes_subtitle,
               itunes_summary,
               itunes_image,
               url PRIMARY KEY,
               type,
               guid,
               description,
               itunes_duration,
               itunes_explicit);""")

URL = "http://78.140.251.40/tmp_audio/itunes2/hik_-_rr_%s.mp3"
FEED = "http://www.radiorecord.ru/rss.xml"
DATEFMT = "%Y-%m-%d"

def download(url, destination):
    fp = open(destination, "wb")
    curl = pycurl.Curl()
    curl.setopt(pycurl.URL, url)
    curl.setopt(pycurl.WRITEDATA, fp)
    curl.perform()
    curl.close()
    fp.close()


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
                self.pubdate = decode(v, 'utf-8')

def get_episode(date):
    result = Episode()
    c = pycurl.Curl()
    c.setopt(c.URL, URL % date.strftime(DATEFMT))
    c.setopt(c.HEADERFUNCTION, result.feed)
    c.setopt(c.NOBODY, True)
    c.perform()
    c.close()
    return result

def load_metadata(feed):
    pubdate = feed['published']
    len_ = feed['links'][0]['length']
    title = feed['title']
    itunes_author = feed['author']
    itunes_subtitle = feed['subtitle']
    itunes_summary = feed['summary']
    itunes_image = feed['image']['href']
    url = feed['links'][0]['href']
    type_ = feed['links'][0]['type']
    guid = feed['id']
    description = ''
    itunes_duration = feed['itunes_duration']
    itunes_explicit = feed['itunes_explicit'] and 'explicit' or 'clean'

    db.execute("""
        INSERT OR REPLACE INTO episodes
        (pubdate, len, title, itunes_author, itunes_subtitle, itunes_summary,
        itunes_image, url, type, guid, description, itunes_duration,
        itunes_explicit)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
        pubdate, len_, title, itunes_author, itunes_subtitle, itunes_summary,
        itunes_image, url, type_, guid, description, itunes_duration,
        itunes_explicit))

def load_id3(url):
    download(url, "/tmp/kih.mp3")
    id3 = eyed3.load("/tmp/kih.mp3")
    title = "{} @ {}".format(id3.tag.artist, id3.tag.title)
    itunes_author = "Radio Record"
    itunes_subtitle = itunes_summary = "Треш-шоу Кремова и Хрусталева"
    itunes_image = "http://www.radiorecord.ru/i/img/rr-logo-podcast.png"
    type_ = "audio/mpeg"
    guid = url
    description = ""
    itunes_duration = str(timedelta(seconds=id3.info.time_secs))
    itunes_explicit = "clean"

    db.execute("""
        UPDATE episodes SET
            title = ?,
            itunes_author = ?,
            itunes_subtitle = ?,
            itunes_summary = ?,
            itunes_image = ?,
            type = ?,
            guid = ?,
            description = ?,
            itunes_duration = ?,
            itunes_explicit = ?
        WHERE url = ?""", (
            title, itunes_author, itunes_subtitle, itunes_summary,
            itunes_image, type_, guid, description, itunes_duration,
            itunes_explicit, url, ))

def load_missing_metadata():
    c = db.execute("SELECT url FROM episodes WHERE title IS NULL LIMIT 1;")
    row = c.fetchone()
    if not row:
        return

    load_id3(row[0])

def mkfeed():
    env = Environment(
        loader=PackageLoader('hik')
    )
    template = env.get_template('rss.xml.tmpl')
    items = db.execute("SELECT * FROM episodes ORDER BY url DESC LIMIT 21")
    print(template.render(items=items))

def fetch():
    feed = feedparser.parse(FEED)
    for item in feed['entries']:
        if 'Хруст' in item['title']:
            load_metadata(item)

def fetch_old():
    start_date = date(2016, 3, 14)
    end_date = date.today()
    for current in daterange(start_date, end_date):
        episode = get_episode(current)
        if episode.exists:
            print("%s: exists!" % current)
            datestr = current.strftime(DATEFMT)
            url = URL % (datestr, )

            db.execute("""INSERT INTO episodes (pubdate, len, url)
                          VALUES (?, ?, ?);""",
                       (episode.pubdate, episode.length, url))

def urls():
    for row in db.execute('SELECT url FROM episodes ORDER BY url'):
        print(row[0])

def print_usage():
    print("Usage: %s <fetch | fetchold | urls>" % argv[0])

args = {
    "fetchold": fetch_old,
    "urls": urls,
    "fetch": fetch,
    "feed": mkfeed,
    "id3": load_missing_metadata
}

if len(argv) == 1:
    print_usage()
else:
    args[argv[1]]()

db.commit()
db.close()
