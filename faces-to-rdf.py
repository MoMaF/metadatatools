#! /usr/bin/env python3

import json
import jsonlines
import configparser
import numpy as np
import pandas as pd
import re
import argparse
import glob
import time
import datetime
import isodate
import rdflib
from pathlib import Path
from urllib.parse import quote
from rdflib.namespace import XSD, RDF, RDFS
from rdflib.plugins.stores import sparqlstore
import requests
from requests.auth import HTTPBasicAuth
from requests.exceptions import ConnectionError, RequestException, HTTPError

QSERVICE = "https://momaf-data.utu.fi:3034/momaf-raw/sparql"
USERVICE = "https://momaf-data.utu.fi:3034/momaf-raw/update"
GRAPH_STORE_URL ="https://momaf-data.utu.fi:3034/momaf-raw/data"

# Name of the named graph for result data
RESULTGRAPH = "http://momaf-data.utu.fi/face_annotation_data"
FILM_FILES_GRAPH_NAME = "http://momaf-data.utu.fi/digital_film_files"

dir = '/scratch/project_2002528'

# Read username and password from INI file. Simple.
config = configparser.ConfigParser()
config.read("momaf.ini")
USERNAME = config["triplestore"]["updateusername"]
PASSWORD = config["triplestore"]["updatepassword"]

parser = argparse.ArgumentParser(description='Dump face detections and recognitions in RDF. Reads username and password from momaf.ini. See momaf.ini.template.')
parser.add_argument('--debug', action='store_true',
                    help='show debug output instead of RDF')
parser.add_argument('--boxdata', action='store_true',
                    help='output **boxdata** rows instead of RDF')
parser.add_argument('--upload',action='store_true',help="Upload data directy to Triple Store. Uploading with argument '--all' replaces the face annotation data graph completely; specifying movie id's on the command line merges data for those movies with existing data in the graph.")
parser.add_argument('--all', action='store_true',help="Process all movies. Overrides any single movie id list present")
parser.add_argument('--datadir', type=str, default=dir+"/emil/data",
                    help="Directory where <movieid>-data directories reside, default=%(default)s")
parser.add_argument('--unlabeled', action='store_true',
                    help="Do not use labels.csv file but predictions.json and clusters.json instead")
parser.add_argument('movies', nargs='*',
                    help='movie-ids ...')
args = parser.parse_args()

if args.debug: print (args)
# if args.upload:
#     store = sparqlstore.SPARQLUpdateStore(auth=(USERNAME,PASSWORD))
#     store.open((QSERVICE,USERVICE))
#     g = rdflib.Graph(store=store,identifier=rdflib.URIRef(RESULTGRAPH))
#     dfg = rdflib.Graph(store=store,identifier=rdflib.URIRef(FILM_FILES_GRAPH_NAME))
#     store.remove_graph(g) # Easiest way to replace the whole set of data is to drop and re-create the graph
#     store.add_graph(g)
# else:
g = rdflib.Graph()
dfg = rdflib.Graph()
    
momaf = rdflib.Namespace("http://momaf-data.utu.fi/")
g.bind("momaf", momaf)
dfg.bind("momaf", momaf)

if not args.unlabeled:
    labels = pd.read_csv('labels.csv')
else:
    labels = None
# actors = pd.read_csv('actors.csv')

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
ares  = store.query(actorquery)

act = {}
for r in ares:
    if args.debug: print ("%s %s %s %s" % r)
    act[int(str(r.elonet_person_id))] = str(r.name)

#if args.debug: print (act)

#print(labels.index)
#print(labels.columns)

def xsdtime(s, fps):
    t = datetime.timedelta(seconds=s/fps)
    l = isodate.time_isoformat(t, format='%H:%M:%S.%f')
    # l = l[:-3]
    # print(s, t, type(t), l, type(l))
    return rdflib.Literal(l, datatype=XSD.time)

def get_digital_film_file(movieid):
    dfquery = """prefix momaf: <http://momaf-data.utu.fi/>
SELECT  ?df WHERE {{ 
  momaf:elonet_elokuva_{} momaf:hasRelatedFile ?df .
  ?df a momaf:DigitalFilmFile. }}
""".format(movieid)
    dfres = store.query(dfquery)
    if args.debug: print (ares[0])
    return URIRef(ares[0])

def make_digital_film_file(movie,filename,swidth,sheight,dwidth,dheight,sar,fps):
    df = momaf["film_file_"+quote(filename)]
    if args.debug: print(filename)
    dfg.add((movie,momaf.hasRelatedFile,df))
    dfg.add((df,RDF.type,momaf.DigitalFilmFile))
    dfg.add((df,momaf.fileName,          rdflib.Literal(filename)))
    dfg.add((df,momaf.storageWidth,      rdflib.Literal(swidth,datatype=XSD.integer)))
    dfg.add((df,momaf.storageHeight,     rdflib.Literal(sheight,datatype=XSD.integer)))
    dfg.add((df,momaf.displayWidth,      rdflib.Literal(dwidth,datatype=XSD.integer)))
    dfg.add((df,momaf.displayHeight,     rdflib.Literal(dheight,datatype=XSD.integer)))
    dfg.add((df,momaf.sampleAspectRatio, rdflib.Literal(sar,datatype=XSD.decimal)))
    dfg.add((df,momaf.framesPerSecond,   rdflib.Literal(fps,datatype=XSD.decimal)))
    if args.debug: print(df)
    return df

if args.all:
    # Get all movie id's from the datadir
    movies = list(map(lambda a : re.match(r".*/(.*)-data$",str(a)).group(1),
                      sorted(Path(args.datadir).glob("*-data"))))
else:
    movies = args.movies

if args.debug: print (list(movies))

for m in movies:
    movie = momaf["elonet_elokuva_"+str(m)]

    if labels is not None:
        l = labels.loc[labels['movie_id']==int(m)]
        l = l.loc[l['cluster_status']=='labeled']
        l = l.loc[l['image_status']=='same']
        nlabels = l.shape[0]
    else:
        l = None
        nlabels = 0

    if args.debug:
        print(m, movie, nlabels, 'labeled trajectories found')
    
    sw  = None
    sh  = None
    dw  = None
    dh  = None
    sar = None
    fps = None

    jf = dir+'/metadata/'+str(m)+'-*.json'
    j  = glob.glob(jf)
    # assert len(j)==1, 'not unique file <'+jf+'> '+str(j)
    assert len(j)>0, 'metadata file <'+jf+'> not found'
    meta = json.load(open(j[0]))
    #print(meta.keys())
    assert 'streams' in meta
    for s in meta['streams']:
        if s['codec_type']=='video':
            assert sw is None and sh is None and fps is None
            sw = int(s['width'])
            sh = int(s['height'])
            a = s.get('sample_aspect_ratio', None)
            if a is None:
                sar = 1
            else:
                x = re.match('(\d+):(\d+)', a)
                if x:
                    assert int(x.group(1))>0 and int(x.group(2))>0
                    sar = int(x.group(1))/int(x.group(2))
                else:
                    sar = float(a)
            assert sar>=1
            dw = int(sar*sw)
            dh = sh
            f = s['avg_frame_rate']
            x = re.match('(\d+)/(\d+)', f)
            if x:
                assert int(x.group(1))>0 and int(x.group(2))>0
                fps = int(x.group(1))/int(x.group(2))
            else:
                fps = float(f)
    assert sw is not None and sh is not None and fps is not None
    assert sw>0 and sh>0 and dw>0 and dh>0 and fps and fps>0

    if args.debug:
        print('sw={} sh={} dw={} dh={} sar={} f={} x={} fps={}'.
              format(sw, sh, dw, dh, sar, f, x, fps))
    
    #get filename
    assert 'format' in meta
    fname = meta['format']['filename'].split("/")[-1]
    assert fname is not None

    # get digital film file
    df = make_digital_film_file(movie,fname,sw,sh,dw,dh,sar,fps)

    d = args.datadir+'/'+str(m)+'-data'

    tra = {}
    if l is not None:
        for _,i in l.iterrows():
            tra[i['trajectory']] = i['label']
            if args.debug:
                print('LABEL', i['trajectory'], i['label'])
    else:
        clupred = {}
        pred = json.load(open(d+'/predictions.json'))
        pred = pred['predictions']
        for t, a in pred.items():
            a = [ (v, k) for k, v in a.items() ]
            a.sort()
            clupred[int(t)] = a[-1][1]
        clus = json.load(open(d+'/clusters.json'))
        for i, c in enumerate(clus['clusters']):
            tra[i] = clupred[c] 
        
    trajl = d+'/trajectories.jsonl'
    if args.debug:
        print('TRAJ', trajl)
    with jsonlines.open(trajl) as tr:
        for l in tr:
            li = l['index']
            if args.debug:
                print(li, l['start'], l['len'], li in tra)
            if li in tra:
                # Annotation starts here
                s = l['start']
                e = s+l['len']-1
                z = re.match('momaf:elonet_henkilo_(\d+)', tra[li])
                assert z
                id = int(z.group(1))
                if args.debug:
                    print('AAA', m, s, e, f, tra[li], id, act[id])
                ann_name = 'annotation_face_{}_{}_{}'.format(m, id, s)
                #ann = rdflib.URIRef(ann)
                if args.debug: print(ann_name)
                ann = momaf[ann_name]
                g.add((ann, RDF.type,       momaf.FaceAnnotation))
                g.add((ann,momaf.annotates,df))
                g.add((ann, momaf.refersTo, momaf['elonet_henkilo_'+str(id)]))
                g.add((ann, momaf.firstFrame,rdflib.Literal(s, datatype=XSD.integer)))
                g.add((ann, momaf.lastFrame,rdflib.Literal(e, datatype=XSD.integer)))
                g.add((movie,momaf.hasAnnotation,ann))

                #BBoxlist
                bboxlistname = "bboxlist_"+ann_name
                bboxlist = momaf[bboxlistname]
                g.add((ann,momaf.bboxlist,bboxlist))
                g.add((bboxlist,RDF.type,RDF.Seq))
                #bbox loop
                b = l['bbs']
                bcount=0
                for f in b:
                    bcount+=1
                    show = s>=82500 and s<84000
                    show = True
                    if show:
                        if args.boxdata:
                            print('**boxdata** {:07d} {} {} retinaface facenet {} {} {} {} 1 face {}'\
                                  .format(int(m), s, s+1, f[0], f[1], f[2], f[3], act[id]))
                        bboxname = "http://momaf-data.utu.fi/boundingbox_{}_{}_{}_{}_{}_{}".format(
                            quote(fname), str(s),f[0],f[1],f[2],f[3])
                        box = rdflib.URIRef(bboxname)
                        g.add((bboxlist, RDF["_"+str(bcount)], box))
                        g.add((box, RDF.type, momaf.BoundingBox))
                        g.add((box, momaf.hasRelatedFile, df))
                        g.add((box, momaf.frameNumber,rdflib.Literal(s,datatype=XSD.integer)))
                        g.add((box, momaf.minX, rdflib.Literal(f[0]/dw, datatype=XSD.decimal)))
                        g.add((box, momaf.minY, rdflib.Literal(f[1]/dh, datatype=XSD.decimal)))
                        g.add((box, momaf.maxX, rdflib.Literal(f[2]/dw, datatype=XSD.decimal)))
                        g.add((box, momaf.maxY, rdflib.Literal(f[3]/dh, datatype=XSD.decimal)))

                    s += 1

if not args.debug and not args.boxdata and not args.upload:
    print(g.serialize(format="turtle").decode("UTF-8"))
    print(dfg.serialize(format="turtle").decode("UTF-8"))

if args.upload:
    auth = HTTPBasicAuth(USERNAME,PASSWORD)
    # Will use N-Triples because that is the fastest to serialize/de-serialize
    head = {'Content-Type':'application/n-triples'}
    # Data graph
    ds = g.serialize(format="nt").decode("UTF-8")
    dparams = {'graph' : RESULTGRAPH}
    # PUT replaces graph; use only if uploading all
    # use POST for adding single film data
    if args.all:
        resp = requests.put(GRAPH_STORE_URL,data=ds,params=dparams,auth=auth,headers=head)
    else:
        resp = requests.post(GRAPH_STORE_URL,data=ds,params=dparams,auth=auth,headers=head)
    print(resp.content)
    # Digital Film Files graph
    dfs = dfg.serialize(format="nt").decode("UTF-8")
    dfparams = {'graph' : FILM_FILES_GRAPH_NAME }
    # POST merges data to existing graph
    resp = requests.post(GRAPH_STORE_URL,data=dfs,params=dfparams,auth=auth,headers=head)
    print(resp.content)
    
