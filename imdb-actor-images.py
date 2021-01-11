#! /usr/bin/env python3

from lxml import html as lxml_html
from lxml import etree
from rdflib.graph import ConjunctiveGraph
from rdflib.namespace import RDF, RDFS, SDO, SKOS
from rdflib import Namespace, URIRef, BNode, Literal
import rdflib
import rdflib_jsonld
import re
from SPARQLWrapper import SPARQLWrapper, JSON
import requests

#print(rdflib.__version__, rdflib_jsonld.__version__)

sparql = SPARQLWrapper("http://momaf-data.utu.fi:3030/momaf-raw/sparql")

momaf_actor_id_map = {}
momaf_movie_id_map = {}

def momaf_actor_id(a):
    if a in momaf_actor_id_map:
        return momaf_actor_id_map[a]

    # ret = a.replace(' ', '_')
    ret = 'https://imdb.com/name/'+a+'/'
    q = """
    prefix momaf: <http://momaf-data.utu.fi/>
    SELECT * WHERE {
      ?sub a momaf:Person; momaf:IMDb_ID ? "IMDBID"
    }
    """
    sparql.setQuery(q.replace('IMDBID', a))
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    for res in results['results']['bindings']:
        #print(res)
        #print (res['sub']['value'])
        ret = res['sub']['value']
        break
    
    momaf_actor_id_map[a] = ret
    return ret

def momaf_movie_id(m):
    if m in momaf_movie_id_map:
        return momaf_movie_id_map[m]

    ret = m.replace(' ', '_')
    q = """
    prefix momaf: <http://momaf-data.utu.fi/>
    SELECT * WHERE {
      ?sub a momaf:Movie; momaf:IMDb_ID ? "IMDBID"
    }
    """
    sparql.setQuery(q.replace('IMDBID', m))
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    for res in results['results']['bindings']:
        #print(res)
        #print (res['sub']['value'])
        ret = res['sub']['value']
        break
    
    momaf_movie_id_map[m] = ret
    return ret

if True:
    url = 'https://imdb.com/title/tt0033798/mediaindex'
    respage = requests.get(url).text
else:
    respage = open('tt0033798.mediaindex').read()

restree = lxml_html.fromstring(respage)

#print(restree)

amap = {}
for i in restree.xpath('//ul[@class="media_index_filter_section"]/li/a'):
    # print(i.attrib['href'], i.text)
    r = re.search('refine=(nm.*)', i.attrib['href'])
    if r:
       #  print(r.group(1), i.text)
        amap[i.text] = r.group(1)

for i in restree.xpath('//script[@type="application/ld+json"]'):
    t = i.text.replace('http://schema.org"', 'https://schema.org/"')
    g = rdflib.Graph().parse(data=t, format='json-ld' )
    #print(g.serialize(format='ttl').decode('utf8'))

    h = rdflib.Graph()
    MOMAF = Namespace('http://momaf-data.utu.fi/')
    h.namespace_manager.bind('momaf', URIRef('http://momaf-data.utu.fi/'))
    h.namespace_manager.bind('skos',  URIRef('http://www.w3.org/2004/02/skos/core#'))

    for s, _, _ in g.triples((None, RDF.type, SDO.ImageObject)):
        a = g.value(s, SDO.caption)
        #print(a)
        j = a.find(' in ')
        if j>=0:
            a = a[:j]
            #aa = a.replace(' ', '_')
            m = g.value(s, SDO.mainEntityOfPage)
            r = re.match('^/title/(.*)/mediaviewer/(.*)$', m)
            assert r, 're.match() failed with <'+m+'>'
            v = r.group(1)
            m = 'imdb_'+r.group(1)+'_'+r.group(2)
            #print(a, m, g.value(s, SDO.contentUrl))
            bn1 = BNode()
            bn2 = BNode()
            h.add((MOMAF[m], RDF.type, MOMAF.Image))
            h.add((MOMAF[m], RDFS.label, Literal(m)))
            h.add((MOMAF[m], SKOS.prefLabel, Literal(m)))
            h.add((MOMAF[m], MOMAF.IMDb_ID, Literal(m)))
            h.add((MOMAF[m], MOMAF.hasMember, bn1))
            h.add((MOMAF[m], MOMAF.hasMember, bn2))
            h.add((MOMAF[m], MOMAF.identifier, Literal(m)))
            h.add((MOMAF[m], MOMAF.recordSource, Literal('IMDb')))
            h.add((MOMAF[m], MOMAF.rights, Literal('ei tiedossa')))
            h.add((MOMAF[m], MOMAF.sourcefile, g.value(s, SDO.contentUrl)))
            h.add((bn1, RDF.type, MOMAF.ImageObject))
            h.add((bn1, MOMAF.hasAgent, URIRef(momaf_movie_id(v))))
            h.add((bn2, RDF.type, MOMAF.ImageObject))
            h.add((bn2, MOMAF.hasAgent, URIRef(momaf_actor_id(amap[a]))))

    print(h.serialize(format='ttl').decode('utf8'))
