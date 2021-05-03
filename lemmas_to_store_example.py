#!/usr/bin/env python3
""" Example of how to update lemmatized text

NB! Required recent rdflib! If you get an error about unknown keyword arguments, update rdflib!

Parser installation and requirements:

## install parser ##
python3 -m venv venv-momaf
source venv-momaf/bin/activate
pip install --upgrade pip
pip install --upgrade setuptools wheel
pip install rdflib
pip install http://dl.turkunlp.org/turku-parser-models/turku_neural_parser-0.3-py3-none-any.whl
pip install torch==1.7.0  # (ignore error of torch 1.7.0 and OpenNMT-py 1.2.0 not being compatible)

## download model ##
wget http://dl.turkunlp.org/turku-parser-models/models_fi_tdt_v2.7.tar.gz
tar zxvf models_fi_tdt_v2.7.tar.gz

## run ##
python lemmas_to_store_example.py 

"""

from tnparser.pipeline import read_pipelines, Pipeline
import re
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
} 
"""
# limit 15


store = sparqlstore.SPARQLUpdateStore(auth=(USERNAME,PASSWORD))
store.open((QSERVICE,USERVICE))
g = Graph(store=store,identifier=URIRef(RESULTGRAPH))

store.remove_graph(g)
store.add_graph(g)
momaf = Namespace("http://momaf-data.utu.fi/")
g.bind("momaf",momaf)

qres = store.query(DATAQUERY)


def load_parser(gpu=True):
    import types
    extra_args=types.SimpleNamespace()
    if gpu:
        extra_args.__dict__["udify_mod.device"]="0" #simulates someone giving a --device 0 parameter to Udify
        extra_args.__dict__["lemmatizer_mod.device"]="0"
    available_pipelines=read_pipelines("models_fi_tdt_v2.7/pipelines.yaml")        # {pipeline_name -> its steps}
    turku_parser=Pipeline(available_pipelines["parse_plaintext"], extra_args)         # launch the pipeline from the steps
    return turku_parser
    
    
def read_conllu(txt):
    sent=[]
    comment=[]
    for line in txt.split("\n"):
        line=line.strip()
        if not line: # new sentence
            if sent:
                yield comment,sent
            comment=[]
            sent=[]
        elif line.startswith("#"):
            comment.append(line)
        else: #normal line
            sent.append(line.split("\t"))
    else:
        if sent:
            yield comment, sent

br_html_regex = re.compile('<br.*?>')
clean_html_regex = re.compile('<.*?>')
def processstring(txt, turku_parser):
    """ This processes each freetext field. Call your stuff from here."""
    
    txt = re.sub(br_html_regex, ' ', txt)
    txt = re.sub(clean_html_regex, '', txt)
    
    ID, FORM, LEMMA, UPOS, XPOS, FEATS, HEAD, DEPREL, DEPS, MISC = range(10)
    parsed = turku_parser.parse(txt)
    lemmatized_sentences = []
    for comm, sent in read_conllu(parsed):
        lemmas = [token[LEMMA] for token in sent if "-" not in token[ID]]
        lemmatized_sentences.append(" ".join(lemmas))
        
    return " ".join(lemmatized_sentences)
    
    
turku_parser = load_parser(gpu=True)

counter = 0
for row in qres:

    content = row[1]
    lemmatized_content = processstring(content, turku_parser)
    #print("Orig:", content, "\n\n")
    #print("Lemm:", lemmatized_content, "\n\n")

    id = row[0]
    content = row[1]
    newcontent = lemmatized_content
    s = URIRef(id)
    p = momaf.lemmatizedText
    o = Literal(newcontent,datatype=XSD.string)
    g.add((s,p,o))
    counter +=1
    
print("Updated", counter, "items!")
    
