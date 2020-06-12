#!/usr/bin/env python3

'''
Copyright (c) 2020 Modul 9/HiFiBerry

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''

import sys
import logging
from pathlib import Path

import mutagen
from mutagen.id3 import PictureType
from mutagen.mp4 import AtomDataType

from musicfiletools.config import MUSICEXT

stats = {}


def cover(directory):
    p = Path(directory)
    for f in p.glob("*.???*"):
        if f.suffix in [".jpg",".jpeg",".png"]:
            if f.stem.lower() in ["folder", "front", "albumart","cover"]:
                return f
    
    return None


def apic_to_file(apic, directory, filebase="cover"):
    if apic.type in [PictureType.COVER_FRONT, PictureType.OTHER]: 
        cover = None
        if apic.mime.lower()=="image/jpeg":
            cover = Path(directory, filebase+".jpg")
        elif apic.mime.lower() == "image/png":
            cover = Path(directory, filebase+".png")
        
        if cover is not None:
            with cover.open("wb") as f:
                f.write(apic.data)
                logging.info(" created %s", cover)
                return True
    
    return False

def covr_to_file(covr, directory, filebase="cover"):
    coverfile = None
    if covr.imageformat == AtomDataType.JPEG:
        coverfile = Path(directory, filebase+".jpg")
    elif covr.imageformat == AtomDataType.PNG:
        coverfile = Path(directory, filebase+".png")
        
    if coverfile is not None:
        with coverfile.open("wb") as f:
            f.write(covr)
            logging.info(" created %s", coverfile)
            return True
    
    return False


def picture_to_file(picture, directory, filebase="cover"):
    coverfile = None
    if picture.mime.lower() == "image/jpeg":
        coverfile = Path(directory, filebase+".jpg")
    elif picture.mime.lower() == "image/png":
        coverfile = Path(directory, filebase+".png")
        
    if coverfile is not None:
        with coverfile.open("wb") as f:
            f.write(picture.data)
            logging.info(" created %s", coverfile)
            return True
    
    return False


def album_data(mutagenFile):
    md = {}
    logging.warn(mutagenFile.keys())
    
    if "TALB" in mutagenFile:
        md["album"]=mutagenFile.get("TALB")
        
    if "TPE2" in mutagenFile:
        md["albumartist"]=mutagenFile.get("TPE2")
    elif "TPE1" in mutagenFile:
        md["albumartist"]=mutagenFile.get("TPE1")
    
    return md
    

def extract_cover_from_files(directory):
    p = Path(directory)
    for f in p.glob("*.???*"):
        if f.suffix.lower() in MUSICEXT:
            try:
                songfile = mutagen.File(f)
                logging.debug(" %s", songfile.keys())
                
                if "APIC:" in songfile.keys():
                    apic = songfile.get("APIC:")
                    if apic_to_file(apic, p):
                        return True
                    
                if "covr" in songfile.keys():
                    cover = songfile.get("covr")[0]
                    if covr_to_file(cover, p):
                        return True
                    
                try:
                    pic = songfile.pictures[0]
                    if picture_to_file(pic, p):
                        return True                
                except:
                    # This is normal as this will only work
                    # with FLAC files
                    pass
                
                logging.info("data: %s ",album_data(songfile))
                    
            except Exception as _e:
                logging.warning("can't handle %s", f)
                
            
    return False
        
    
def has_music(directory):
    p = Path(directory)
    for f in p.glob("*.???*"):
        if f.suffix.lower() in MUSICEXT:
            return True
        
    return False
        
        
def process_directory(directory, depth=30):
    
    global stats
    
    p = Path(directory)
    
    if depth>0:
        for d in p.glob("*"):
            if d.is_dir():
                process_directory(d, depth-1)
                
    if has_music(p):
        logging.debug("found music in %s",p)
        
        c = cover(p)
        if c is None:
            logging.debug("no cover found")
            if extract_cover_from_files(p):
                stats["coversExtracted"]=stats.get("coversExtracted",0)+1
                logging.info("got cover for %s",p)
                
        else:
            logging.debug("cover: %s", c)
            
        albumjson=Path(p,"album.json")
        try:
            with open(albumjson) as json_file:
                albumdata = json.load(json_file)
                


if __name__ == '__main__':
    
    directory="."
    
    loggingconf=False
    
    if len(sys.argv) > 1:
        if "-v" in sys.argv:
            logging.basicConfig(format='%(levelname)s: %(name)s - %(message)s',
                                level=logging.DEBUG)
            loggingconf=True
            logging.info("enabled verbose logging")
            
        for a in sys.argv:
            if Path(a).is_dir():
                directory=a
                
    if not(loggingconf):
            logging.basicConfig(format='%(levelname)s: %(name)s - %(message)s',
                        level=logging.INFO)
                    
    p=Path(directory).absolute()
    logging.info("Extracting covers from %s",p)
    process_directory(p)
    
    logging.info("Stats: %s", stats)