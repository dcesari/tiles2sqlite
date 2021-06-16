#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import glob
import sqlite3
import datetime
    

def generate_osmand(self):
    """
    Generate a sqlite database containing the generated tiles in the format
    for OsmAnd application
    https://osmand.net/help-online/technical-articles#OsmAnd_SQLite_Spec

    Expected variables:
    title, minzoom, maxzoom, publishurl
    """

    if self.options.profile != 'mercator': return
    if not os.path.exists(self.output):
        os.makedirs(self.output)
    try:
        os.unlink(os.path.join(self.output, "osmand.sqlite"))
    except:
        pass

    conn = sqlite3.connect(os.path.join(self.output, "osmand.sqlite"))
    curs = conn.cursor()
                           
    curs.execute("CREATE TABLE tiles (x int, y int, z int, s int, image blob, time timestamp, PRIMARY KEY (x,y,z,s))")
    curs.execute("CREATE INDEX IND on tiles (x,y,z)")
    curs.execute("CREATE TABLE info(url,rule,tilenumbering,timeSupported,expireminutes int,ellipsoid int,minzoom int,maxzoom int,referer)")
    curs.execute("CREATE TABLE info(maxzoom int, minzoom int)")
    curs.execute("INSERT INTO info values (?,?,?,?,?,?,?,?,?)",
                  ("", "", "", "no", 525600, 0,
                   17-self.tmaxz, 17-self.tminz, ""))

    for tilename in glob.glob(os.path.join(self.output, "*", "*", "*.*")):
        try:
            # reconstruct coordinates from path .../z/x/y.png
            s = os.path.split(tilename) # .../z/x, y.png
            y = int(s[1].split(".")[0])
            s = os.path.split(s[0]) # .../z, x
            x = int(s[1])
            s = os.path.split(s[0]) # ..., z
            z = int(s[1])
            y = 2**z - 1 - y
            z = 17 - z
            curs.execute("INSERT INTO tiles values (?,?,?,?,?,?)",
                         (x, y, z, 0, sqlite3.Binary(buffer(open(tilename).read())),
                          datetime.datetime(2019,1,1)))
            if self.options.verbose:
                print(tilename,x,y,z)
        except ValueError:
            # not a tile?
            pass
        
    curs.execute("INSERT INTO info (maxzoom, minzoom) SELECT max(z),min(z) from tiles")
    conn.execute("VACUUM")
    conn.commit()
    curs.close()


def generate_mbtiles(tileroot, output, name=None):
    """
    Generate a sqlite database containing the generated tiles in the
    mbtiles format https://github.com/mapbox/mbtiles-spec

    Expected variables:
    title, minzoom, maxzoom, publishurl
    """

    try:
        os.unlink(output)
    except:
        pass

    if name is None: name = os.path.split(output)[1]
    conn = sqlite3.connect(output)
    curs = conn.cursor()
    curs.execute("CREATE TABLE metadata (name text, value text)")
    curs.execute("CREATE TABLE tiles (zoom_level integer, tile_column integer, tile_row integer, tile_data blob)")
    curs.execute("CREATE UNIQUE INDEX tile_index on tiles (zoom_level, tile_column, tile_row)")

    curs.execute("INSERT INTO metadata values (?,?)", ("name", name))
#    la1, lo1 = self.mercator.MetersToLatLon(self.ominx, self.ominy)
#    la2, lo2 = self.mercator.MetersToLatLon(self.omaxx, self.omaxy)
#    curs.execute("INSERT INTO metadata (?,?)", ("bounds",
#                "%f, %f, %f, %f" % (lo1, la1, lo2, la2)))
#    curs.execute("INSERT INTO metadata (?,?)", ("center",
#                "%f, %f, %d" % ((lo1+lo2)/2., (la1+la2)/2., self.tminz)))

    format = None
    maxzoom = 0
    minzoom = 32
    for tilename in glob.glob(os.path.join(tileroot, "*", "*", "*.???")):
        try:
            # reconstruct coordinates from path .../z/x/y.png
            s = os.path.split(tilename) # .../z/x, y.png
            if not s[1].endswith("png") and not s[1].endswith("jpg"):
                continue
            print(s)
            if format is None: format = s[1].split(".")[1]
            y = int(s[1].split(".")[0])
            s = os.path.split(s[0]) # .../z, x
            x = int(s[1])
            s = os.path.split(s[0]) # ..., z
            z = int(s[1])
            y = 2**z - 1 - y
            maxzoom = max(z, maxzoom)
            minzoom = min(z, minzoom)
            print(tilename,z,x,y)
            curs.execute("INSERT INTO tiles values (?,?,?,?)",
                         (z, x, y, sqlite3.Binary(open(tilename, "rb").read())))
#            if self.options.verbose:
#                print(tilename,x,y,z)
        except (ValueError, IndexError):
            # not a tile?
            pass

    if format is not None:
        curs.execute("INSERT INTO metadata values (?,?)", ("format", format))
    curs.execute("INSERT INTO metadata values (?,?)", ("minzoom", minzoom))
    curs.execute("INSERT INTO metadata values (?,?)", ("maxzoom", maxzoom))
    # curs.execute("INSERT INTO info values (maxzoom, minzoom) SELECT max(z),min(z) from tiles")

    conn.commit()
    conn.execute("VACUUM")
    curs.close()


def main():
    generate_mbtiles("villanders", "villanders.mbtiles")
    
if __name__ == '__main__':
    main()

