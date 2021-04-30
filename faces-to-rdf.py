#! /usr/bin/env python3

import json
import jsonlines
import numpy as np
import pandas as pd
import re
import argparse
import time
import datetime
import isodate
import rdflib
from rdflib.namespace import XSD, RDF, RDFS
from rdflib.plugins.stores import sparqlstore

QSERVICE = "https://momaf-data.utu.fi:3034/momaf-raw/sparql"
USERVICE = "https://momaf-data.utu.fi:3034/momaf-raw/update"
USERNAME = "updater"
# Set password in local instance
PASSWORD = "***secret***"

# Name of the named graph for result data
RESULTGRAPH = "http://momaf-data.utu.fi/face_annotation_data"

parser = argparse.ArgumentParser(description='Dump face detections and recognitions in RDF.')
parser.add_argument('--debug', action='store_true',
                    help='show debug output instead of RDF')
parser.add_argument('--boxdata', action='store_true',
                    help='output **boxdata** rows instead of RDF')
parser.add_argument('--upload',action='store_true',help="Upload data directy to Triple Store")
parser.add_argument('movies', nargs='+',
                    help='movie-ids ...')
args = parser.parse_args()

if args.upload:
    store = sparqlstore.SPARQLUpdateStore(auth=(USERNAME,PASSWORD))
    store.open((QSERVICE,USERVICE))
    g = rdflib.Graph(store=store,identifier=rdflib.URIRef(RESULTGRAPH))

    store.remove_graph(g) # Easiest way to replace the whole set of data is to drop and re-create the graph
    store.add_graph(g)
else:
    g = rdflib.Graph()
    
momaf = rdflib.Namespace("http://momaf-data.utu.fi/")
g.bind("momaf", momaf)

labels = pd.read_csv('labels.csv')
actors = pd.read_csv('actors.csv')

### Get actor names etc. from triple store
actorquery = """
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
prefix momaf: <http://momaf-data.utu.fi/>
prefix skos: <http://www.w3.org/2004/02/skos/core#>
select * where {
  ?person_uri a momaf:Person; 
  momaf:elonet_ID ?elonet_id ; 
  momaf:elonet_person_ID ?elonet_person_id; 
  skos:prefLabel ?name }
"""

store = sparqlstore.SPARQLStore(QSERVICE)
ares = store.query(actorquery)

act = {}
for r in ares:
    if args.debug: print ("%s %s %s %s" % r)
    act[int(str(r.elonet_person_id))] = str(r.name)

if args.debug: print (act)

#print(labels.index)
#print(labels.columns)

def xsdtime(s, fps):
    t = datetime.timedelta(seconds=s/fps)
    l = isodate.time_isoformat(t, format='%H:%M:%S.%f')
    # l = l[:-3]
    # print(s, t, type(t), l, type(l))
    return rdflib.Literal(l, datatype=XSD.time)

for m in args.movies:
    l = labels.loc[labels['movie_id']==int(m)]
    l = l.loc[l['cluster_status']=='labeled']
    l = l.loc[l['image_status']=='same']

    fps = 24
    tra = {}
    for _,i in l.iterrows():
        tra[i['trajectory']] = i['label']
    
    d = '/scratch/project_2002528/emil/data/'+m+'-data'
    trajl = d+'/trajectories.jsonl'
    with jsonlines.open(trajl) as tr:
        for l in tr:
            # print(l)
            li = l['index']
            if li in tra:
                s = l['start']
                b = l['bbs']
                for f in b:
                    show = s>=82500 and s<84000
                    show = True
                    if show:
                        z = re.match('momaf:elonet_henkilo_(\d+)', tra[li])
                        assert z
                        id = int(z.group(1))
                        #print(m, s, f, tra[li], act[id])
                        if args.boxdata:
                            print('**boxdata** {} {} {} retinaface facenet {} {} {} {} 1 face {}'\
                                  .format(m, s, s+1, f[0], f[1], f[2], f[3], act[id]))
                        ann = 'annotation_face_{}_{}_{}'.format(m, id, s)
                        #ann = rdflib.URIRef(ann)
                        ann = momaf[ann]
                        g.add((ann, RDF.type,       momaf.FaceAnnotation))
                        g.add((ann, momaf.ofMovie,  momaf['elonet_elokuva_'+str(m)]))
                        g.add((ann, momaf.hasAgent, momaf['elonet_henkilo_'+str(id)]))

                        med = rdflib.BNode()
                        g.add((ann, momaf.hasMedia, med))
                        g.add((med, RDF.type,       momaf.DigitalFilmFile))
                        g.add((med, momaf.fileUrl,  rdflib.URIRef('optional')))
                        g.add((med, momaf.fileName, rdflib.URIRef('optional')))
                        g.add((med, RDFS.label,     rdflib.Literal('optional')))

                        box = rdflib.BNode()
                        g.add((ann, momaf.hasBoundinxBox, box))
                        g.add((box, momaf.minX,     rdflib.Literal(f[0], datatype=XSD.decimal)))
                        g.add((box, momaf.minY,     rdflib.Literal(f[1], datatype=XSD.decimal)))
                        g.add((box, momaf.maxX,     rdflib.Literal(f[2], datatype=XSD.decimal)))
                        g.add((box, momaf.maxY,     rdflib.Literal(f[3], datatype=XSD.decimal)))

                        g.add((ann, momaf.annotationStartTime, xsdtime(s,   fps)))
                        g.add((ann, momaf.annotationEndTime,   xsdtime(s+1, fps)))
                    s += 1

if not args.debug and not args.boxdata and not args.upload:
    print(g.serialize(format="turtle").decode("UTF-8"))
