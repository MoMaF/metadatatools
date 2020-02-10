#! /usr/bin/env python3

# 117212 117213 117163

import sys
import urllib.request
import re
import xml.etree.ElementTree as ET

for id in sys.argv[1:]:
    #id = '117163'
    s = urllib.request.urlopen('https://elonet.finna.fi/Record/kavi.elonet_elokuva_'+id).read().decode()
    # s = open('kavi.elonet_elokuva_'+id).read()
    # print(s)

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

    # print(a)
    # print(a, file=open('raw-raw-'+id+'.xml', 'w'))

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

    # print(a, file=open('raw-'+id+'.xml', 'w'))

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
    
