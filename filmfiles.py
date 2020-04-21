#! /usr/bin/env python3

import sys
import glob
import pandas as pd
import rdflib
from rdflib import Namespace, URIRef, BNode, Literal
from rdflib.graph import ConjunctiveGraph
from rdflib.namespace import RDF, RDFS, OWL, XSD, DCTERMS

g = ConjunctiveGraph()
g.bind("dcterms", DCTERMS)

movie = "http://elonet.finna.fi/movie#"

def handle_one(f):
    v = '/scratch/project_2002528/films/'+str(f.elonet_id)+'[-_]*'
    # print(f, v)
    v = glob.glob(v)
    if len(v)==0:
        v = ['not found']
    v = v[0]
    av = 'https://a3s.fi/momaf/'+v[25:]
    picsom_label = ('000000'+str(f.elonet_id))[-7:]
    picsom_uri = 'http://picsom.aalto.fi/momaf/'+picsom_label
    quality = f.quality
    uri = URIRef(movie+str(f.elonet_id))
    g.add((uri, DCTERMS.date,        Literal(f.date, datatype=XSD.date)))
    g.add((uri, DCTERMS.contributor, Literal(f.provider)))
    g.add((uri, DCTERMS.medium,      Literal(v)))
    g.add((uri, DCTERMS.medium,      Literal(av)))
    g.add((uri, DCTERMS['format'],   Literal("video/mp4")))
    g.add((uri, DCTERMS.relation,    Literal(picsom_uri)))
    g.add((uri, Literal("quality"),  Literal(quality)))

assert len(sys.argv)==2, 'Exactly one argument <filename.tsv> is required'
    
columns=['elonet_id', 'name', 'date', 'provider', 'quality']
df = pd.read_csv(sys.argv[1], sep='\t', names=columns, parse_dates=[2])
# print(df)
for i in df.itertuples():
    handle_one(i)
    
print(g.serialize(format='turtle').decode())
