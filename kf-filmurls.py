#! /usr/bin/env python3

import sys
import argparse
import requests
import xml.etree.ElementTree as ET
import html
from lxml import html as lxml_html

description=r"""Read list of films and the XML data files from the National Filmography

Parses the elonet.finna.fi -rss feed and collects all film URL:s and respective XML data dumps that refer to the Elonet database.

With relevant option, the list of url's is printed to file 'kf-filmurls.txt'
"""

filmographyurl_full = "https://elonet.finna.fi/Search/Results?sort=main_date_str+asc&filter%5B%5D=%7Ebuilding%3A%221%2FKAVI%2Fskf%2F%22&type=AllFields&view=rss"

filmographyurl_test = "https://elonet.finna.fi/Search/Results?sort=main_date_str+asc&filter%5B%5D=%7Ebuilding%3A%221%2FKAVI%2Fskf%2F%22&filter%5B%5D=%7Eformat%3A%221%2FVideo%2FShort%2F%22&filter%5B%5D=online_boolean%3A%221%22&type=AllFields&view=rss"

parser = argparse.ArgumentParser(description=description)
parser.add_argument('--debug',action="store_true",help="Print intermediate data to stdout")
parser.add_argument('--csvoutput',action="store_true",help="Save URL's to kf-filmurls.txt")
parser.add_argument('--fulldata',action="store_true",help="Get full data. Otherwise only a set of 10 movies.")
args = parser.parse_args()

ns = {'atom':'http://www.w3.org/2005/Atom',
      'dc':'http://purl.org/dc/elements/1.1/',
      'slash':'http://purl.org/rss/1.0/modules/slash',
      'opensearch':'http://a9.com/-/spec/opensearch/1.1/'}

if args.fulldata:
    filmographyurl=filmographyurl_full
else:
    filmographyurl=filmographyurl_test
    
def parse_and_collect(url):
    if args.debug: print(url)
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

def get_and_save_xml(url):
    if args.debug: print(url)
    respage = requests.get(url).text
    restree = lxml_html.fromstring(respage)
    prestring = restree.xpath(".//pre[@id='record-data']/text()")[0].strip()
    if args.debug:
        with open("debug.xml","w") as f:
            f.write(prestring)
    xmltree = ET.fromstring(prestring)
    filmid = xmltree.find(".//CinematographicWork/Identifier[@IDTypeName='elonet_elokuva']").text
    if args.debug: print(filmid)
    ET.ElementTree(xmltree).write(filmid+".xml",encoding="UTF-8",xml_declaration=True)
    
urllist = list(map(lambda l: l.text,parse_and_collect(filmographyurl)))
if args.csvoutput:
    with open('kf-filmurls.txt','w') as of:
        of.write("\n".join(urllist))
if args.debug: print (urllist)
list(map(get_and_save_xml,urllist))
