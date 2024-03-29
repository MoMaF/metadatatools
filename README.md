# metadatatools

Scripts for extracting and handling KAVI's Elonet and MoMaF metadata.

## `faces-to-rdf.py`

Tool for processing face recognition data.

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

## `elonet-person-data.py`

This script first collects all production members for the national filmography movies, using the MoMaF sparql endpoint at https://momaf-data.utu.fi:3034/momaf-raw/sparql . It then reads through the Elonet person pages that are accessible at URL http://elonet.fi/fi/henkilo/[elonet_person_id], parses the HTML and gathers information about birth and death as well as the occasionally longish textual descriptions for the person in question. This information is converted to RDF according to the MoMaF ontology, and the data is output as Turtle to the standard output.

The properties the produced data uses are:
- `bdatestring`: Birthdate as string. Should be encoded as XML schema Date, datatype xsd:date, but this requires a complex parser, for the original data is so bad. Easier to update the data later on.
- `bplace`: Birth place, as string
- `ddatestring`: Date of death as string. See commend for `bdatestring` about what should be done later.
- `dplace`: Death place, as string
- `summary`: Summary or textual description, as datatype rdf:HTML

The script takes a long time to run, several hours, because it reads each person page from the Elonet database.

There are no options for the script. Redirect standard output to a file to store the data. The script outputs a percentage of the current stage to standard error.

## `elonet-person-data-clean.py`

This script cleans the data produced by `elonet-person-data.py`. It parses the date fields for correct dates and adds two fields to the dataset:

- `bdate`: Birthdate as XSD:Date
- `date`: Date of death as XSD:Date

Should be run on the data file output by `elonet-person-data.py`.

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
from the triple store to Python as JSON.lemmas_to_store_example.py

## `sparql_get_person_image_links.py`

Queries the SPARQL endpoint at http://momaf-data.utu.fi:3030/momaf-raw/sparql and retrieves the data connecting individual persons and still images. The query returns more than just the necessary fields; whenever creating data that should be fed back to the database, either the field `PersonElonetID` or the IRI in `person` should be used. The name is not necessarily good enough for uniquely identifying the person.

The same applies for `filmname`and `filmID`; for example, search for name "Seitsemän veljestä" return more than one entry.

This is not a complete tool, but a demonstration of how to get data out of the triple store.

## `lemmas_to_store_example.py`

Shows how to update data at the triple store. Password provided on a need-to-have basis on request.

Graph name is important, while it keeps your dataset coherent. Links work between graphs, so one graph can only contain the data that is needed.

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
xmlstarlet tr ../sparql/xml-to-html-momaf.xsl tmp.xml > metadata-links-of-momaf-actors.html
```

