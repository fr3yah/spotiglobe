import sqlite3

conn = sqlite3.connect('artist.db')

c = conn.cursor()

c.execute("""CREATE TABLE artists (id text, artist text, area text)""")

conn.commit()

conn.close()
