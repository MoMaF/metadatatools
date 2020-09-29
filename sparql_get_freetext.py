#!/usr/bin/python3

# sparql_get_freetext.py

# Script base for retrieving the Content description, Synopsis and Review data from the MoMaF triple store.

from SPARQLWrapper import SPARQLWrapper, JSON

sparql = SPARQLWrapper("http://momaf-data.utu.fi:3030/momaf-raw/sparql")

# This is the query to get the data. The size of result set is limited
# to 3. If you want the whole data, remove 'limit 3' from the query
# string below.
sparql.setQuery("""
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
prefix skos-core: <http://www.w3.org/2004/02/skos/core#>
prefix momaf: <http://momaf-data.utu.fi/>

select ?filmiri ?id ?year ?synopsis ?description ?review
where
{ ?filmiri a momaf:Movie ; momaf:elonet_movie_ID ?id ; skos-core:prefLabel ?name; momaf:productionyear ?year.
  optional { ?filmiri  momaf:contentDescription [ rdfs:label "Synopsis"@fi; rdfs:comment ?synopsis ] }
  optional { ?filmiri momaf:contentDescription [ rdfs:label "Content description"@fi; rdfs:comment ?description ] }
  optional { ?filmiri momaf:review ?review }
  .
} limit 3
""")

sparql.setReturnFormat(JSON)
results = sparql.query().convert()

# How to get the result content for 'synopsis' for the first film
print(results['results']['bindings'][0]['synopsis'])


# Looping over all results
for res in results['results']['bindings']:
    print (res['filmiri']['value'])
