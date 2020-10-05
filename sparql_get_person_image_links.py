#! /usr/bin/env python3

# sparql_get_freetext.py

# Script base for retrieving the Content description, Synopsis and Review data from the MoMaF triple store.

from SPARQLWrapper import SPARQLWrapper, JSON

sparql = SPARQLWrapper("http://momaf-data.utu.fi:3030/momaf-raw/sparql")

# This is the query to get the data. The size of result set is limited
# to 10. If you want the whole data, remove 'limit 10' from the query
# string below.
#
# the columns:
#
# person: IRI for the person entry in the triple store
# name: name of the person as string
# PersonElonetID: ID number of the person in the Elonet database
# image: IRI for the image entry in the triple store
# filmname: name of the film from which the still image is taken
# filmID: ID number for the film; the only unique way to connect back to film data
# image_url: url for the actual image file on the Elonet server.

sparql.setQuery("""
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
prefix momaf: <http://momaf-data.utu.fi/>

SELECT ?person ?name ?PersonElonetID ?image ?filmname ?filmID ?image_url WHERE {
  ?person a momaf:Person; rdfs:label ?name; momaf:elonet_person_ID ?PersonElonetID .
  ?image a momaf:Image ; momaf:hasAgent ?person ; momaf:sourcefile ?image_url .
  ?image momaf:hasAgent ?film .
  ?film a momaf:Movie .
  ?film skos:prefLabel ?filmname; momaf:elonet_movie_ID ?filmID .
} having (?name!=?PersonElonetID)
limit 10
""")

sparql.setReturnFormat(JSON)
results = sparql.query().convert()


# Looping over all results
for res in results['results']['bindings']:
    print (res['name']['value']+" "+res['image_url']['value'])
