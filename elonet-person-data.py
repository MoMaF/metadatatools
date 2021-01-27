#!/usr/bin/env python3

import rdflib
from SPARQLWrapper import SPARQLWrapper,JSON
import lxml.html
import lxml.etree
import urllib.request
from rdflib.namespace import XSD, RDF
import datetime
import math
import sys
import re

g = rdflib.Graph()

momaf = rdflib.Namespace("http://momaf-data.utu.fi/")
g.bind("momaf",momaf)

propmap = {'Syntymäaika':momaf.bdatestring,
           'Syntymäpaikka':momaf.bplace,
           'Kuolinaika':momaf.ddatestring,
           'Kuolinpaikka':momaf.dplace
           }


def parseelonetpage(res,g):
    """Parse elonet page, take info from person id. First argument is query result, second is the graph"""
    elopid = res['eloid']['value']
    # print(elopid)
    subject = rdflib.URIRef(res['sub']['value'])
    tr = lxml.html.parse(urllib.request.urlopen("http://elonet.fi/fi/henkilo/"+elopid))
    root = tr.getroot()
    tb = root.xpath('//table[@class="table table-finna-record record-details"]')
    for tbi in tb:
        for n in propmap.keys():
            bd = tbi.xpath("tr/th[contains(.,'"+n+"')]/../td/text()")
            if len(bd)>0:
                # This is for setting the datatype for dates. Requires a date parser,
                # which is complicated, because original data is so BAD! See "parsedate" above.
                #    if (propmap[n]==momaf.bdate or propmap[n]==momaf.ddate):
                #        g.add((subject,propmap[n],rdflib.Literal(parsedate(bd[0]),datatype=XSD.date)))
                #    else:
                g.add((subject,propmap[n],rdflib.Literal(bd[0])))
    sums = root.xpath('//div[contains(@class,"recordSummary")]/p[not(@class)]')
    for sum1 in sums:
        g.add((subject,momaf.summary,rdflib.Literal(lxml.etree.tostring(sum1,encoding="UTF-8").decode(),datatype=RDF.HTML)))

mraw = SPARQLWrapper("https://momaf-data.utu.fi:3034/momaf-raw/sparql")

mraw.setQuery("""
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
prefix momaf: <http://momaf-data.utu.fi/>

SELECT ?sub (sample(?nimi) as ?n) ?eloid (count(?sub) as ?elos) WHERE {
  #bind (<http://momaf-data.utu.fi/elonet_henkilo_100004> as ?sub) .
  ?sub a momaf:Person; skos:prefLabel ?nimi;  momaf:elonet_person_ID ?eloid; ^momaf:hasAgent [ ^momaf:hasMember ?f ]. 
  ?f a momaf:Movie .
  #minus { service <https://query.wikidata.org/sparql> {
  #    ?wikibaseid wdt:P2387 ?eloid .}
  #}
} group by ?sub ?eloid
#having (?elos>1)
#order by desc (?elos)
#limit 10
""")

mraw.setReturnFormat(JSON)
results = mraw.query().convert()
l = len(results['results']['bindings'])
i = 0
for res in results['results']['bindings']:
    parseelonetpage (res,g)
    i+=1
    if (i % 10 == 0):
        print(str(math.trunc((i/l)*100))+" %",file=sys.stderr)
    
print(g.serialize(format="turtle").decode("utf-8"))
