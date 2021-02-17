#!/usr/bin/env python3
""" Example of how to update lemmatized text

NB! Required recent rdflib! If you get an error about unknown keyword arguments, update rdflib!

"""


from rdflib import Graph,Literal,URIRef,Namespace
from rdflib.namespace import XSD
from rdflib.plugins.stores import sparqlstore

#from SPARQLWrapper import SPARQLWrapper,JSON

QSERVICE = "https://momaf-data.utu.fi:3034/momaf-raw/sparql"
USERVICE = "https://momaf-data.utu.fi:3034/momaf-raw/update"
USERNAME = "updater"
PASSWORD = "***secret***"

RESULTGRAPH = "http://momaf-data.utu.fi/lemmatized_texts"


"""
The following works for testing, but to get all data, remove the limit at the end.


The query finds all nodes that have the data property 'text' and returns the content of that text.

"""

DATAQUERY = """PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX text: <http://jena.apache.org/text#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
prefix momaf:  <http://momaf-data.utu.fi/>

select ?id ?content where {
  ?id momaf:text ?content .
} limit 15
"""


store = sparqlstore.SPARQLUpdateStore(auth=(USERNAME,PASSWORD))
store.open((QSERVICE,USERVICE))
g = Graph(store=store,identifier=URIRef(RESULTGRAPH))

store.remove_graph(g)
store.add_graph(g)
momaf = Namespace("http://momaf-data.utu.fi/")
g.bind("momaf",momaf)

qres = store.query(DATAQUERY)

def processstring(st):
    """ This processes each freetext field. Call your stuff from here."""
    return st[::-1]

for row in qres:
    id = row[0]
    content = row[1]
    newcontent = processstring(content)
    s = URIRef(id)
    p = momaf.lemmatizedText
    o = Literal(newcontent,datatype=XSD.string)
    g.add((s,p,o))
    
