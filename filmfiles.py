#! /usr/bin/env python3

import sys
import pandas as pd
import rdflib
from rdflib import Namespace, URIRef, BNode, Literal
from rdflib.graph import ConjunctiveGraph
from rdflib.namespace import RDF, RDFS, OWL, XSD

g = ConjunctiveGraph()

WD  = Namespace("http://www.wikidata.org/entity/")         ; g.bind("wd",  WD )
WDT = Namespace("http://www.wikidata.org/prop/direct/")    ; g.bind("wdt", WDT)
P   = Namespace("http://www.wikidata.org/prop/"  )         ; g.bind("p",   P  )
PS  = Namespace("http://www.wikidata.org/prop/statement/") ; g.bind("ps",  PS )
PQ  = Namespace("http://www.wikidata.org/prop/qualifier/") ; g.bind("pq",  PQ )

elonet = "http://elonet.finna.fi/"
movie  = elonet+"movie#"

def handle_one(f):
    # print(f)
    v = '/scratch/project_xxx/'+str(f.elonet_id)+'.mp4'
    uri = URIRef(movie+str(f.elonet_id))
    g.add((uri, RDFS.label, Literal(f.Index)))
    g.add((uri, WDT.P31,    Literal(v)))   # instance of * film
    g.add((uri, WDT.P577,   Literal(f.date, datatype=XSD.date))) # publication date
        # g.add((uri, WDT.P2346,  Literal(id)))                    # Elonet movie ID
    g.add((uri, WDT.P272,   Literal(f.provider)))                    # production company
    g.add((uri, WDT.P57,    Literal(f.quality)))                            # director

assert len(sys.argv)==2, 'Exactly one argument <filename.tsv> is required'
    
columns=['elonet_id', 'name', 'date', 'provider', 'quality']
df = pd.read_csv(sys.argv[1], sep='\t', names=columns, parse_dates=[2])
# print(df)
for i in df.itertuples():
    handle_one(i)
    
print(g.serialize(format='turtle').decode())
