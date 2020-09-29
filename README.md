# metadatatools

Scripts for extracting and handling KAVI's Elonet and MoMaF metadata.

## `kavi-download`

Downloads all XML files listed inside the script.  Change switch really=0
to really=1 to really download instead of just telling the files should be
downloaded.

`kavi-download` invokes `rip-xml.py` for each movie individually

## `rip-xml.py`

Downloads Elonet HTMLs and rips the inlined XML for any number of
films whose IDs are given on the command line.  Argument `--debug`
forces storing of `ID-raw-raw.xml` and `ID-raw.xml` versions too.

## `xml2rdf.py`

Reads in XML files on the command line and prints to STDOUT Turtle RDF
knowledge graph of all movies and persons (actors and directors) found
in them.  With arguments `--movies` and `--persons` prints only those
nodes.  Links from movies to directors, actors and characters are
stored in the movie nodes, whereas the person nodes are quite empty.

## `kf-filmurls.py`

Reads the national filmography data from https://elonet.finna.fi/, and
parses the pages for url links to Elonet database. List of url's is
saved to file `kf-filmurls.txt`, if chosen by option, and the xml
files are saved in current directory, just like `rip-xml.py`. These
files can then be given to `xml2rdf.py` for further processing.

Run `kf-filmurls.py --help` for information on arguments. By default,
loads only a selection of 10 files.

## `sparql_get_freetext.py`

Queries the SPARQL endpoint at
http://momaf-data.utu.fi:3030/momaf-raw/sparql and retrieves the
contents of Synopsis, Content description and Review for all movies. 

This is not a complete tool but a demonstration of how to get data
from the triple store to Python as JSON.

## examples

```bash
./kavi-download
./xml2rdf.py *.xml > all.ttl
sparql --data=all.ttl --query=../sparql/momaf-films.sq
sparql --data=all.ttl --query=../sparql/actors-top-100.sq
sparql --data=all.ttl --query=../sparql/tuntematon-sotilas-1955-roles.sq
sparql --data=all.ttl --query=../sparql/wikidata-of-momaf-films.sq
```

## HTML output

```bash
sparql --data=all.ttl --query=../sparql/wikidata-of-momaf-films.sq --results=xml > tmp.xml
xmlstarlet tr ../sparql/xml-to-html-momaf.xsl tmp.xml > wikidata-of-momaf-films.html

sparql --data=all.ttl --query=../sparql/metadata-links-of-momaf-films.sq --results=xml > tmp.xml
xmlstarlet tr ../sparql/xml-to-html-momaf.xsl tmp.xml > metadata-links-of-momaf-films.html

sparql --data=all.ttl --query=../sparql/metadata-links-of-momaf-actors.sq --results=xml > tmp.xml
xmlstarlet tr ../sparql/xml-to-html-momaf.xsl tmp.xml > metadata-links-of-momaf-actors.html
```

