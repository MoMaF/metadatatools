# metadatatools

Scripts for extracting and handling KAVI's Elonet and MoMaF metadata.

## `kavi-download`

Downloads all XML files listed inside the script.  Change switch really=0
to really=1 to really download instead of just telling the files should be
downloaded.

`kavi-download` invokes `rip-xml.py` for each movie individually

## `kf-to-rdf.xslt`

XSLT template for converting XML files from the Elonet database to
RDF/XML using the MoMaF ontology. These can be used by almost RDF tool
and uploaded to triple stores.

Use SaxonHE or similar XSL processor with XSLT 3.0 support to convert.

## `ontology/MoMaF-ontology.xml`

The MoMaF ontology in RDF/XML format. This file has been saved from
Protégé (5.5.0), and is used as such by the triple store for making
inferences based on the data.

This file can offer insights as to how metadata is organized.

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

Uses SPARQLWrapper, from https://rdflib.dev/sparqlwrapper/ 

This is not a complete tool but a demonstration of how to get data
from the triple store to Python as JSON.

## `sparql_get_person_image_links.py`

Queries the SPARQL endpoint at http://momaf-data.utu.fi:3030/momaf-raw/sparql and retrieves the data connecting individual persons and still images. The query returns more than just the necessary fields; whenever creating data that should be fed back to the database, either the field `PersonElonetID` or the IRI in `person` should be used. The name is not necessarily good enough for uniquely identifying the person.

The same applies for `filmname`and `filmID`; for example, search for name "Seitsemän veljestä" return more than one entry.

This is not a complete tool, but a demonstration of how to get data out of the triple store.


## examples

```bash
./kavi-download
./xml2rdf.py *.xml > all.ttl
sparql --data=all.ttl --query=../sparql/momaf-films.rq
sparql --data=all.ttl --query=../sparql/actors-top-100.rq
sparql --data=all.ttl --query=../sparql/tuntematon-sotilas-1955-roles.rq
sparql --data=all.ttl --query=../sparql/wikidata-of-momaf-films.rq
```

### Converting Elonet XML to RDF
Requirements:
- `kf-to-rdf.xsl` file in this repository
- JAR of Saxon-HE XSLt Processor (See https://www.saxonica.com/download/java.xml). Saxon-HE is the open source version, with somewhat limited functionality but fully suitable for this purpose.

How to run:
```bash
java -jar saxon-he-10.2.jar -xsl:kf-to-rdf.xslt -threads:3 -t -s:kf-data/ -o:kf-data-rdf/
```

Explanations:
- jar: expects to find the downloaded Saxon-HE JAR file in current directory. Paths can be used
- xsl: name of the XSL file to use
- threads: How many CPU cores to use. Speeds up the process considerable is >1, but see how many you have available
- s: Source diredtory. Transforms all *.xml files in this directory
- o: Target directory. Resulting RDF/XML files are placed in this directory. If same as source, original files may be overwritten.

## HTML output

```bash
sparql --data=all.ttl --query=../sparql/wikidata-of-momaf-films.rq --results=xml > tmp.xml
xmlstarlet tr ../sparql/xml-to-html-momaf.xsl tmp.xml > wikidata-of-momaf-films.html

sparql --data=all.ttl --query=../sparql/metadata-links-of-momaf-films.rq --results=xml > tmp.xml
xmlstarlet tr ../sparql/xml-to-html-momaf.xsl tmp.xml > metadata-links-of-momaf-films.html

sparql --data=all.ttl --query=../sparql/metadata-links-of-momaf-actors.rq --results=xml > tmp.xml
xmlstarlet tr ../sparql/xml-to-html-momaf.xsl tmp.xml | sed 's/&amp;/\&/g' > metadata-links-of-momaf-actors.html
```

