#! /usr/bin/env python3

import json
import jsonlines
import numpy as np
import pandas as pd
import re
import argparse
import glob
import time
import datetime
import isodate
import rdflib
from urllib.parse import quote
from rdflib.namespace import XSD, RDF, RDFS
from rdflib.plugins.stores import sparqlstore
import requests
from requests.auth import HTTPBasicAuth
from requests.exceptions import ConnectionError, RequestException, HTTPError

QSERVICE = "https://momaf-data.utu.fi:3034/momaf-raw/sparql"
USERVICE = "https://momaf-data.utu.fi:3034/momaf-raw/update"
GRAPH_STORE_URL ="https://momaf-data.utu.fi:3034/momaf-raw/data"
USERNAME = "updater"
# Set password in local instance
PASSWORD = "***secret***"

# Name of the named graph for result data
RESULTGRAPH = "http://momaf-data.utu.fi/object_annotation_data"
FILM_FILES_GRAPH_NAME = "http://momaf-data.utu.fi/digital_film_files"

dir = '/scratch/project_2002528'

parser = argparse.ArgumentParser(description='Dump object recognitions in RDF.')
parser.add_argument('--debug', action='store_true',
                    help='show debug output instead of RDF')
parser.add_argument('--threshold', type=float, default=0.25,
                    help="Threshold value, default %(default)s")
parser.add_argument('--upload',action='store_true',help="Upload data directy to Triple Store")
parser.add_argument('movies', nargs='+',
                    help='boxdata-files ...')
args = parser.parse_args()

g = rdflib.Graph()
dfg = rdflib.Graph()
    
momaf = rdflib.Namespace("http://momaf-data.utu.fi/")
g.bind("momaf", momaf)
dfg.bind("momaf", momaf)

def xsdtime(s, fps):
    t = datetime.timedelta(seconds=s/fps)
    l = isodate.time_isoformat(t, format='%H:%M:%S.%f')
    # l = l[:-3]
    # print(s, t, type(t), l, type(l))
    return rdflib.Literal(l, datatype=XSD.time)

def make_digital_film_file(movie,filename,fwidth,fheight,fps):
    df = momaf["film_file_"+quote(filename)]
    if args.debug: print(filename)
    dfg.add((movie,momaf.hasRelatedFile,df))
    dfg.add((df,RDF.type,momaf.DigitalFilmFile))
    dfg.add((df,momaf.fileName,rdflib.Literal(filename)))
    dfg.add((df,momaf.frameWidth,rdflib.Literal(fwidth,datatype=XSD.int)))
    dfg.add((df,momaf.frameHeight,rdflib.Literal(fheight,datatype=XSD.int)))
    dfg.add((df,momaf.framesPerSecond,rdflib.Literal(fps,datatype=XSD.decimal)))
    if args.debug: print(df)
    return df

for b in args.movies:
    w   = None
    h   = None
    fps = None
    xno = 0

    for ll in open(b):
        if False and args.debug:
            print(ll)

        rm = re.search('boxdata.. (\d+) (\d+) (\d+) detectron2 detectron2'
                       +' (\d+) (\d+) (\d+) (\d+) ([\d\.]+) (.+)$', ll)
        if not rm:
            continue
        mnumb = int(rm.group(1))
        frame = int(rm.group(2))

        tlx = int(rm.group(4))
        tly = int(rm.group(5))
        brx = int(rm.group(6))
        bry = int(rm.group(7))

        score = float(rm.group(8))
        obj   = rm.group(9)
        keep  = score>=args.threshold
        # print(mnumb, frame, obj, score, keep)
        if not keep:
            continue

        if args.debug:
            print(mnumb, frame, tlx, tly, brx, bry, obj, score, keep)

        m = mnumb
        if fps is None:
            movie = momaf["elonet_elokuva_"+str(m)]
            jf = dir+'/metadata/'+str(m)+'-*.json'
            j  = glob.glob(jf)
            # assert len(j)==1, 'not unique file <'+jf+'> '+str(j)
            assert len(j)>0, 'metadata file <'+jf+'> not found'
            meta = json.load(open(j[0]))
            # print(meta.keys())
            assert 'streams' in meta
            for s in meta['streams']:
                if s['codec_type']=='video':
                    w = int(s['width'])
                    h = int(s['height'])
                    f = s['avg_frame_rate']
                    x = re.match('(\d+)/(\d+)', f)
                    if x:
                        assert int(x.group(1))>0 and int(x.group(2))>0
                        fps = int(x.group(1))/int(x.group(2))
                    else:
                        fps = float(f)
                        
            assert w is not None and h is not None and fps is not None
            assert w>0 and h>0 and fps and fps>0

            #get filename
            assert 'format' in meta
            fname = meta['format']['filename'].split("/")[-1]
            assert fname is not None

            # get digital film file
            df = make_digital_film_file(movie,fname,w,h,fps)
        if args.debug:
            print('ANNO', m, w, h, fps, df, obj, frame, xno)
            
        ann_name = 'annotation_object_{}_{}_{}_{}'.format(m, obj, frame, xno)
        xno += 1
        if args.debug:
            print(ann_name)
        ann = momaf[ann_name]
        g.add((ann, RDF.type,          momaf.ObjectAnnotation))
        g.add((ann, momaf.annotates,   df))
        g.add((ann, momaf.firstFrame,  rdflib.Literal(frame, datatype=XSD.int)))
        g.add((ann, momaf.lastFrame,   rdflib.Literal(frame, datatype=XSD.int)))
        g.add((ann, momaf.minX,        rdflib.Literal(tlx/w, datatype=XSD.decimal)))
        g.add((ann, momaf.minY,        rdflib.Literal(tly/h, datatype=XSD.decimal)))
        g.add((ann, momaf.maxX,        rdflib.Literal(brx/w, datatype=XSD.decimal)))
        g.add((ann, momaf.maxY,        rdflib.Literal(bry/h, datatype=XSD.decimal)))
        g.add((ann, momaf.objectClass, rdflib.Literal(obj)))
        g.add((ann, momaf.score,       rdflib.Literal(score, datatype=XSD.decimal)))
        g.add((movie,momaf.hasAnnotation,ann))

if not args.debug and not args.upload:
    print(g.serialize(format="turtle").decode("UTF-8"))
    print(dfg.serialize(format="turtle").decode("UTF-8"))

if args.upload:
    auth = HTTPBasicAuth(USERNAME,PASSWORD)
    # Will use N-Triples because that is the fastest to serialize/de-serialize
    head = {'Content-Type':'application/n-triples'}
    # Data graph
    ds = g.serialize(format="nt").decode("UTF-8")
    dparams = {'graph' : RESULTGRAPH}
    # PUT replaces graph
    # Better not do that; merge changes instead
    resp = requests.post(GRAPH_STORE_URL,data=ds,params=dparams,auth=auth,headers=head)
    print(resp.content)
    # Digital Film Files graph
    dfs = dfg.serialize(format="nt").decode("UTF-8")
    dfparams = {'graph' : FILM_FILES_GRAPH_NAME }
    # POST merges data to existing graph
    resp = requests.post(GRAPH_STORE_URL,data=dfs,params=dfparams,auth=auth,headers=head)
    print(resp.content)
    
