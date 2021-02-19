#!/usr/bin/env python3
""" Example of how to update NER results to triple store

NB! Required recent rdflib! If you get an error about unknown keyword arguments, update rdflib!

"""


from rdflib import Graph,Literal,URIRef,Namespace
from rdflib.namespace import XSD,RDFS,RDF
from rdflib.plugins.stores import sparqlstore

from urllib.parse import quote

#from SPARQLWrapper import SPARQLWrapper,JSON

QSERVICE = "https://momaf-data.utu.fi:3034/momaf-raw/sparql"
USERVICE = "https://momaf-data.utu.fi:3034/momaf-raw/update"
USERNAME = "updater"
PASSWORD = "***secret***"

"""All produced data is placed in this named graph which is completely
replaced on each run of the script.

"""
RESULTGRAPH = "http://momaf-data.utu.fi/NER_results"


"""The following works for testing, but to get all data, remove the
limit at the end.

The query finds all nodes that have the data property 'text' and
returns the content of that text.

If you want to use data in lemmatized text fields, replace
'momaf:text' with 'momaf:lemmatizedText'

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
    nes = [  # Example of return data
        {'name': 'Helsinki','type':'GPE'},
        {'name': 'Antti Viljanen','type':'PERSON'},
        {'name': 'Antto Viljanen','type':'PERSON'}
    ]
    return nes


for row in qres:
    id = row[0]
    s = URIRef(id)
    content = row[1]
    nes = processstring(content)
    for ne in nes:
        namelocal = quote(ne['name'])
        nametype = quote(ne['type'])
        nename = URIRef("http://momaf-data.utu.fi/NEname_{}_{}".format(namelocal,nametype))
        nelabel = Literal(ne['name'],datatype=XSD.string)
        netype = URIRef("http://momaf-data.utu.fi/NEtype_{}".format(nametype))

        g.add((netype,RDF.type,momaf.NamedEntityType))
        g.add((nename,RDF.type,momaf.NamedEntity))
        g.add((nename,RDFS.label,nelabel))
        g.add((nename,momaf.hasNamedEntityType,netype))
        g.add((s,momaf.mentionsNamedEntity,nename))
    
"""
"Named Entity" is defined as a combination of the name and type of the entity. This means, that words 'suomalaisen' and 'suomalaisten' result in different entities because the name differs. If lemmatization is able to normalize the strings, then better results might come from using the field 'lemmatizedText' in the SPARQL query above.
"""
