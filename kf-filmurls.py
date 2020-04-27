#! /usr/bin/env python3

import sys
import argparse
import requests
import xml.etree.ElementTree as ET

description=r"""Read list of films from the National Filmography

Parses the elonet.finna.fi -rss feed and collects all film URL:s that refer to the Elonet database.

The list of url's is printed to file 'kf-filmurls.txt'
"""

filmographyurl = "https://elonet.finna.fi/Search/Results?sort=main_date_str+asc&filter%5B%5D=%7Ebuilding%3A%221%2FKAVI%2Fskf%2F%22&type=AllFields&view=rss"

parser = argparse.ArgumentParser(description=description)
parser.add_argument('--debug',action="store_true",help="Print intermediate data to stdout")

args = parser.parse_args()

ns = {'atom':'http://www.w3.org/2005/Atom',
      'dc':'http://purl.org/dc/elements/1.1/',
      'slash':'http://purl.org/rss/1.0/modules/slash',
      'opensearch':'http://a9.com/-/spec/opensearch/1.1/'}

def parse_and_collect(url):
    respage = requests.get(url).text
    restree = ET.fromstring(respage)
    reslist = restree.findall(".//item/link",ns)
    if args.debug: print (list(map (lambda l: print (l.text),reslist)))
    next = restree.findall(".//atom:link[@rel='next']",ns)
    if (next):
        if args.debug: print (next[0].attrib['href'])
        return (reslist + parse_and_collect(next[0].attrib['href']))
    else:
        return (reslist)

with open('kf-filmurls.txt','w') as of:
    of.write("\n".join(list(map(lambda l: l.text,parse_and_collect(filmographyurl)))))
