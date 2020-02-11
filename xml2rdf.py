#! /usr/bin/env python3

import sys, re, argparse
import xml.etree.ElementTree as ET
import rdflib
from rdflib import Namespace, URIRef, BNode, Literal
from rdflib.graph import ConjunctiveGraph
from rdflib.namespace import RDF, RDFS, OWL, XSD

parser = argparse.ArgumentParser(description='Process Elonet XMLs.')
parser.add_argument('--movies', action='store_true',
                    help='produce output for (only) movies')
parser.add_argument('--persons', action='store_true',
                    help='produce output for (only) persons')
parser.add_argument('--debug', action='store_true',
                    help='show debug output instead of RDF')
parser.add_argument('files', nargs='+',
                    help='file.XML ...')
args = parser.parse_args()
if not args.movies and not args.persons:
    args.movies = args.persons = True

elonet = "http://elonet.finna.fi/"
movie  = elonet+"movie#"
person = elonet+"person#"

g   = ConjunctiveGraph()

WD  = Namespace("http://www.wikidata.org/entity/")         ; g.bind("wd",  WD )
WDT = Namespace("http://www.wikidata.org/prop/direct/")    ; g.bind("wdt", WDT)
P   = Namespace("http://www.wikidata.org/prop/"  )         ; g.bind("p",   P  )
PS  = Namespace("http://www.wikidata.org/prop/statement/") ; g.bind("ps",  PS )
PQ  = Namespace("http://www.wikidata.org/prop/qualifier/") ; g.bind("pq",  PQ )

def clean(s):
    if s is None:
        return None
    s = ' '.join(s.split('\n'))
    while s.find('  ')!=-1:
        s = ' '.join(s.split('  '))
    while s[0]==' ':
        s = s[1:]
    while s[-1]==' ':
        s = s[:-1]
    return s

pe = []

for f in args.files:
    if args.debug:
        print('STARTING', f)

    root = ET.parse(f).getroot()
    cw   = root.findall("./CinematographicWork/Identifier[@IDTypeName='elonet_elokuva']/..")[0]

    if args.movies:
        id = cw.findall("./Identifier")[0].text
        ti = cw.findall("./IdentifyingTitle")[0].text
        yr = int(cw.findall("./YearOfReference")[0].text)
        dn = cw.findall("./HasAgent/Activity[@tehtava='ohjaus']/../AgentName")[0].text
        dr = cw.findall("./HasAgent/Activity[@tehtava='ohjaus']/../AgentIdentifier/IDValue")[0].text
        pr = cw.findall("./HasAgent[@elonet-tag='elotuotantoyhtio']/AgentName")[0].text
        if args.debug:
            print(id, ti, dr, dn, pr, yr)

        uri = URIRef(movie+id)
        urd = URIRef(person+dr)
        g.add((uri, RDFS.label, Literal(ti)))
        g.add((uri, WDT.P31,    P.Q11424))                       # instance of * film
        g.add((uri, WDT.P577,   Literal(yr, datatype=XSD.date))) # publication date
        g.add((uri, WDT.P2346,  Literal(id)))                    # Elonet movie ID
        g.add((uri, WDT.P272,   Literal(pr)))                    # production company
        g.add((uri, WDT.P57,    urd))                            # director
        pe.append((dr, dn))

        for a in cw.findall("./HasAgent[@elonet-tag='elonayttelija']"):
            i = a.findall("./AgentIdentifier/IDValue")[0].text
            n = a.findall("./AgentName")[0].text
            r = a.findall("./AgentName")[0].attrib.get('elokuva-elonayttelija-rooli', None);
            n = clean(n)
            r = clean(r)
            if args.debug:
                print('    kred', i, n, r)

            urx = BNode()
            ura = URIRef(person+i)
            g.add((uri, P.P161,  urx))            # cast member
            g.add((urx, PS.P161, ura))            # cast member
            if r is not None:
                g.add((urx, PQ.P453, Literal(r))) # character role
            pe.append((i, n))
            
        for a in cw.findall("./HasAgent[@elonet-tag='elokreditoimatonnayttelija']"):
            i = a.findall("./AgentIdentifier/IDValue")
            if len(i):
                i = i[0].text
                n = a.findall("./AgentName")[0].text
                r = a.findall("./AgentName")[0].attrib.get('elokuva-elokreditoimatonnayttelija-rooli', None);
                n = clean(n)
                r = clean(r)
                if args.debug:
                    print(' ei-kred', i, n, r)

                if i is not None and n is not None:
                    urx = BNode()
                    ura = URIRef(person+i)
                    g.add((uri, P.P161,  urx))
                    g.add((urx, PS.P161, ura))
                    if r is not None:
                        g.add((urx, PQ.P453, Literal(r)))
                    pe.append((i, n))

        if args.debug:
            print()

x = set()
if args.movies:
    for i, n in pe:
        if args.debug:
            print('    pers', i, n)
        if i in x:
            continue;
        x.add(i)
        ura = URIRef(person+i)
        g.add((ura, RDFS.label, Literal(n)))
        g.add((ura, WDT.P31,    P.Q215627))  # instance of * person
        g.add((ura, P.P2387,    Literal(i))) # Elonet person ID

if not args.debug:
    print(g.serialize(format='turtle').decode())

