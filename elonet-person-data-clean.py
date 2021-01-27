#!/usr/bin/env python3

import rdflib
from rdflib.namespace import XSD, RDF
import argparse
import re
import datetime

description=r"""Semantify the string data in Elonet person data

Processes the dataset read by elonet-person-data.py further.
"""

parser = argparse.ArgumentParser(description=description)
parser.add_argument('--infile',type=argparse.FileType('r',encoding="UTF-8"),help="Person data from Elonet, as Turtle output from elonet-person-data.py")
parser.add_argument('--debug',action="store_true",help="Print debugging info")

args = parser.parse_args()

momaf = rdflib.Namespace("http://momaf-data.utu.fi/")

g = rdflib.Graph()
g.bind("momaf",momaf)

g.parse(args.infile,format="turtle")

def parsedate (d1):
    #d2 = d1.replace("00.00.","")
    d3 = d1.split(",",1)[0]
    d2 = re.sub(r'([\D^]*)(00)(\.)',r'\1\3',d3)
    d = re.sub(r'(.*\d{4})(00)(.*)',r'\1\3',d2).strip('.')
    try:
        tm = datetime.datetime.strptime(d,'%d.%m.%Y')
    except ValueError:
        try:
            tm = datetime.datetime.strptime(d,'%m.%Y')
        except ValueError:
            try:
                tm = datetime.datetime.strptime(d,'%d.%m.%y')
                if tm.year>2000:
                    tm = tm.replace(year=tm.year-100)
            except ValueError:
                try:
                    tm = datetime.datetime.strptime(d,'%y')
                    if tm.year>2000:
                        tm = tm.replace(year=tm.year-100)
                except ValueError:
                    try:
                        tm = datetime.datetime.strptime(d,'%Y%m')
                    except ValueError:
                        try:
                            tm = datetime.datetime.strptime(d,'%Y')
                        except ValueError:
                            tm = datetime.datetime.strptime(d,'..%Y')
    return tm.date()

i= 0
qres = g.query(
    """select ?s ?o where {
       ?s momaf:bdatestring ?o
    }""")

for res in qres:
    i+=1
    if args.debug: print("B{}: {} | {}".format(i, res[0],res[1]))
    g.add((res[0],momaf.bdate,rdflib.Literal(parsedate(res[1]),datatype=XSD.date)))

qres = g.query(
    """select ?s ?o where {
       ?s momaf:ddatestring ?o
    }""")

for res in qres:
    i+=1
    if args.debug: print("D{}: {} | {}".format(i, res[0],res[1]))
    g.add((res[0],momaf.ddate,rdflib.Literal(parsedate(res[1]),datatype=XSD.date)))

print(g.serialize(format="turtle").decode("UTF-8"))


