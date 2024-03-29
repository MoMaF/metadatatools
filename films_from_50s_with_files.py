#! /usr/bin/env python3

# films_from 50s_with_files.py
# Script to return all 50s films with file names of the actual film files

from SPARQLWrapper import SPARQLWrapper, JSON

sparql = SPARQLWrapper("http://momaf-data.utu.fi:3030/momaf-raw/sparql")

# This is the query to get the data. 
sparql.setQuery("""
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX text: <http://jena.apache.org/text#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
prefix momaf:  <http://momaf-data.utu.fi/>

select distinct ?film ?elonet_movie_id ?year ?filename where { 
  ?film momaf:productionyear ?year .
  ?film momaf:elonet_movie_ID ?elonet_movie_id .
  ?film momaf:hasRelatedFile [ a momaf:DigitalFilmFile; momaf:fileName ?filename ]
  filter (xsd:int(?year)>1949 && xsd:int(?year)<1960)
} order by ?year
""")

sparql.setReturnFormat(JSON)
results = sparql.query().convert()

# Returned fields:

# film: the film URI used by the triple store. Please
#  carry this data along, it helps to reconnect the results to the film
#  data.

# elonet_movie_id: simple id for internal use, if you need

# year: "Official" production year. May not be the same as the year of the premiere

# filename: name of the film file in the momaf data directory
#  /scratch/project/2002528/films

# Looping over all results
for res in results['results']['bindings']:
    print ("Film: "+res['film']['value']+", File: "+res["filename"]["value"])
