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
import argparse
import time
import os

#print(rdflib.__version__, rdflib_jsonld.__version__)

debug = False

sparql = SPARQLWrapper("http://momaf-data.utu.fi:3030/momaf-raw/sparql")

momaf_actor_id_map = {}
momaf_movie_id_map = {}
imdb_movie_id_map  = {}

momaf_http = 'http://momaf-data.utu.fi/'

def show_dicts():
    dd = [('momaf_actor_id_map', momaf_actor_id_map),
          ('momaf_movie_id_map', momaf_movie_id_map),
          ('imdb_movie_id_map ', imdb_movie_id_map)]
    for n, m in dd:
        for k, v in m.items():
            print(n, k, v)

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

def imdb_movie_id(m):
    if m in imdb_movie_id_map:
        return imdb_movie_id_map[m]

    ret = None
    q = """
    prefix momaf: <http://momaf-data.utu.fi/>
    SELECT * WHERE {
      <ELONETID> momaf:IMDb_ID ?imdbid .
    }
    """
    q = q.replace('ELONETID', m)
    # print(q)
    sparql.setQuery(q)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    # print(results)
    for res in results['results']['bindings']:
        #print(res)
        #print (res['imdbid']['value'])
        ret = res['imdbid']['value']
        break
    
    imdb_movie_id_map[m] = ret
    return ret

def all_imdb_ids():
    q = """
    prefix momaf: <http://momaf-data.utu.fi/>
    SELECT * WHERE {
      ?uri a momaf:Movie ; 
           momaf:IMDb_ID ?imdbid .
    }
    """
    sparql.setQuery(q)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    # print(results)
    ret = []
    for res in results['results']['bindings']:
        #print(res)
        #print (res['imdbid']['value'])
        uri    = res['uri'   ]['value']
        imdbid = res['imdbid']['value']
        ret.append(imdbid)
        imdb_movie_id_map[uri] = imdbid
    return ret

def fetch_one(url):
    momaf_film = momaf_http+'elonet_elokuva_'
    if url.find(momaf_film)==0:
        url = imdb_movie_id(url)
        # print(url)
        if url is None:
            return

    suff = '/mediaindex'
    if url.isnumeric():
        url = 'tt'+url
    if url[:4]!='http':
        url = 'https://imdb.com/title/'+url
    while url[-1:]=='/':
        url = url[:-1]
    if url[-len(suff):]!=suff:
        url += suff

    if True:
        respage = requests.get(url).text
    else:
        respage = open('tt0033798.mediaindex').read()

    restree = lxml_html.fromstring(respage)

    #print(restree)

    amap = {}
    for i in restree.xpath('//ul[@class="media_index_filter_section"]/li/a'):
        if debug:
            print(i.attrib['href'], i.text)
        r = re.search('refine=(nm.*)', i.attrib['href'])
        if r:
            if debug:
                print(r.group(1), i.text)
            amap[i.text] = r.group(1)

    h = rdflib.Graph()
    MOMAF = Namespace(momaf_http)
    h.namespace_manager.bind('momaf', URIRef(momaf_http))
    h.namespace_manager.bind('skos',  URIRef('http://www.w3.org/2004/02/skos/core#'))

    for i in restree.xpath('//script[@type="application/ld+json"]'):
        t = i.text.replace('http://schema.org"', 'https://schema.org/"')
        g = rdflib.Graph().parse(data=t, format='json-ld' )
        #print(g.serialize(format='ttl').decode('utf8'))

        for s, _, _ in g.triples((None, RDF.type, SDO.ImageObject)):
            a = g.value(s, SDO.caption)
            if debug:
                print(a)
            if a.find(' and ')!=-1 or a.find(' & ')!=-1 or a.find(' directing ')!=-1:
                continue
            j = a.find(' in ')
            if j>=0:
                a = a[:j]
                j = a.find(' as ')
                if j>=0:
                    a = a[:j]
                if not a in amap:
                    print(a, 'not found in actors')
                    continue
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
    return h

if __name__ == '__main__':
    # url = 'https://imdb.com/title/tt0033798/mediaindex'
    # url = 'http://momaf-data.utu.fi/elonet_elokuva_105505'

    parser = argparse.ArgumentParser(description='Solves actor imge URLs form IMDb.')
    parser.add_argument('url', nargs='+',
                        help='URLs or IMDb actor IDs')

    args = parser.parse_args()
    urls = args.url
    if len(urls)==1 and urls[0]=='ALL':
        urls = all_imdb_ids()
    #urls = urls[:3]
        
    for i, url in enumerate(urls):
        file = url.replace(':', '_').replace('/', '_')+'.ttl'
        print(str(i)+'/'+str(len(urls)), url, '=>', file, flush=True)
        if os.path.isfile(file):
            continue
        h = fetch_one(url)
        out = open(file, 'w')
        print('#', url+'\n', file=out)
        print(h.serialize(format='ttl').decode('utf8'), file=out)
        time.sleep(2)
              
    #show_dicts()
    
