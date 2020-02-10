#! /usr/bin/env python3

import sys, re, argparse
import urllib.request
import xml.etree.ElementTree as ET

parser = argparse.ArgumentParser(description='Rip Elonet XMLs.')
parser.add_argument('--debug', action='store_true',
                    help='store "raw" debug versions')
parser.add_argument('files', nargs='+',
                    help='file.XML ...')
args = parser.parse_args()

for id in args.files:
    print('STARTING', id)
    #id = '117163'

    url = 'https://elonet.finna.fi/Record/kavi.elonet_elokuva_'+id
    req = urllib.request.Request(url)
    try: urllib.request.urlopen(req)
    except urllib.error.URLError as e:
        print(e.reason)
        print()
        continue
    
    s = urllib.request.urlopen(req).read().decode()
    sx = '&lt;?xml version=&quot;1.0&quot;?&gt;'
    ex = '&lt;/ExchangeSet&gt;'

    a = ''
    b = False
    for l in s.split('\n'):
        # print('xxx', l)
        if l[:len(sx)]==sx:
            b = True
        if b:
            a += l
        if l[:len(ex)]==ex:
            break

    if args.debug:
        print(a, file=open(id+'-raw-raw.xml', 'w'))

    a = re.sub('&lt;', '<', a)
    a = re.sub('&gt;', '>', a)
    a = re.sub('&quot;', '"', a)
    a = re.sub('&#xC5;', 'Å', a)
    a = re.sub('&#xC4;', 'Ä', a)
    a = re.sub('&#xD6;', 'Ö', a)
    a = re.sub('&#xE5;', 'å', a)
    a = re.sub('&#xE4;', 'ä', a)
    a = re.sub('&#xF6;', 'ö', a)
    a = re.sub('&#039;', "'", a)
    a = re.sub('&amp;', '&', a)
    a = re.sub('<\?xml version="1.0"\?>', '<?xml version="1.0" encoding="utf-8"?>', a)

    if args.debug:
        print(a, file=open(id+'-raw.xml', 'w'))

    root = ET.fromstring(a)
    ET.ElementTree(root).write(id+'.xml', encoding='utf-8', xml_declaration=True)

    t = '+++'
    for title in root.iter('Title'):
        if 'lang' not in title[0].attrib and \
           title[1].attrib.get('elokuva-elonimi-tyyppi', '') == 'virallinen nimi':
            t = title[0].text
    print('{} [{}]'.format(t, id))

    for agent in root.iter('HasAgent'):
        if agent.attrib.get('elonet-tag', '')=='elonayttelija':
            n = '***'
            r = '???'
            i = '#'
            # print(agent)
            for name in agent.iter('AgentName'):
                n = name.text
                if 'elokuva-elonayttelija-rooli' in name.attrib:
                    r = name.attrib['elokuva-elonayttelija-rooli']
            for identifier in agent.iter('AgentIdentifier'):
                for value in identifier.iter('IDValue'):
                    i = value.text
            print('  {} ({}) [{}]'.format(n, r, i))

    print()
    
