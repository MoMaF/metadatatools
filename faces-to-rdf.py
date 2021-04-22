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

parser = argparse.ArgumentParser(description='Dump face detections and recognitions in RDF.')
parser.add_argument('--debug', action='store_true',
                    help='show debug output instead of RDF')
parser.add_argument('--boxdata', action='store_true',
                    help='output **boxdata** rows instead of RDF')
parser.add_argument('movies', nargs='+',
                    help='movie-ids ...')
args = parser.parse_args()

momaf = rdflib.Namespace("http://momaf-data.utu.fi/")
g = rdflib.Graph()
g.bind("momaf", momaf)

labels = pd.read_csv('labels.csv')
actors = pd.read_csv('actors.csv')

act = {}
for _,i in actors.iterrows():
    act[i['id']] = i['name']

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

if not args.debug and not args.boxdata:
    print(g.serialize(format="turtle").decode("UTF-8"))
