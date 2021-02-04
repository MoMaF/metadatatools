<?xml version="1.0" encoding="UTF-8"?>
<!-- XSLT to transform Elonet metadata to RDF using MoMaF ontology structure.

Harri Kiiskinen for MoMaF project, 2021.

Changes:

Since 0.2:
- Add PrivateScreening. These were not recognized before and resulted in extra momaf:date fields. Should be compatible.
- Parse durations and lengths properly. Durations are as XSD, lengths are in meters
- Convert illeage month and day string ("00") to legal ("01")
- normalize unicode to NFC in select fields. This should be automated for all, but may not be possible
- remove illegal date 0000-00-00
- Fix broadcast data: date, place, audience
- add datatype declarations to durations
-->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="3.0"
		xmlns:xs="http://www.w3.org/2001/XMLSchema"
		xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
		xmlns:momaf="http://momaf-data.utu.fi/"
		xmlns:momafsubject="http://momaf-data.utu.fi/subject/"
		xmlns:momafmovietype="http://momaf-data.utu.fi/movietype/"
		xmlns:momafgenre="http://momaf-data.utu.fi/genre/"
		xmlns:momafadminplace="http://momaf-data.utu.fi/adminplace#"
		xmlns:dc="http://purl.org/dc/elements/1.1/"
		xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#"
		xmlns:elonet-film="https://elonet.finna.fi/Record/kavi."
		xmlns:elonet-kuva="http://www.elonet.fi/tenho/media"
		xmlns:skos="http://www.w3.org/2004/02/skos/core#"
		xmlns="http://www.w3.org/1999/xhtml/">
  <xsl:output method="xml" indent="yes"/>
  <!-- Limit only to ExcangeSets that contain a film where the type is
       different from documentary ('dokumentti') In a discussion
       during Fall 2020 it was decided, that also the metadata set
       should be limited to fiction films. On inspection of the
       metadata set, it became clear that the easiest and most robust
       way was to exclude the metadata for films classified as
       documentaries. Other classifications are overlapping. -->
  <xsl:template match="ExchangeSet[descendant::ProductionEvent[@elonet-tag='laji2fin']/elokuva_laji2fin/text()!='dokumentti']">
    <rdf:RDF>
      <xsl:apply-templates/>
    </rdf:RDF>
  </xsl:template>
  <xsl:template match="ExchangeSet">
    <rdf:RDF/>
  </xsl:template>
  <xsl:template name="path">
    <xsl:for-each select="parent::*">
      <xsl:call-template name="path"/>
    </xsl:for-each>
    <xsl:value-of select="name()"/>
    <xsl:text>/</xsl:text>
  </xsl:template>

  <xsl:template match="text()">
    <xsl:value-of select="normalize-unicode(.)"/>
  </xsl:template>
  <!-- Mapping from Elonet language terms to ISO two-letter forms.
  -->
  <xsl:variable name="langmap">
    <momaf:orig key="bul">bg</momaf:orig>
    <momaf:orig key="eng">en</momaf:orig>
    <momaf:orig key="fin">fi</momaf:orig>
    <momaf:orig key="fre">fr</momaf:orig>
    <momaf:orig key="ger">de</momaf:orig>
    <momaf:orig key="heb">he</momaf:orig>
    <momaf:orig key="ita">it</momaf:orig>
    <momaf:orig key="jpn">ja</momaf:orig>
    <momaf:orig key="spa">es</momaf:orig>
    <momaf:orig key="swe">sv</momaf:orig>
    <momaf:orig key="ukr">uk</momaf:orig>
  </xsl:variable>

  <!-- Mapping from Elonet participant roles to MoMaF ontology classes.
  -->
  <xsl:variable name="agentmap">
    <momaf:orig name="" expl="A99">ImageObject</momaf:orig>
    <momaf:orig name="avustajat" expl="A99">Extras</momaf:orig>
    <momaf:orig name="eloepisodi" expl="A99">FilmEpisode</momaf:orig>
    <momaf:orig name="eloesiintyja" expl="E99">Performer</momaf:orig>
    <momaf:orig name="eloesiintyjakokoonpano" expl="oth">PerformerGroup</momaf:orig>
    <momaf:orig name="elokreditoimatonesiintyja" expl="E99">PerformerNonCredited</momaf:orig>
    <momaf:orig name="elokreditoimatonnayttelija" expl="E01">ActorNonCredited</momaf:orig>
    <momaf:orig name="elokreditoimatontekija" expl="A08">PhotographerNonCredited</momaf:orig>
    <momaf:orig name="elokreditoimatontekija" expl="A13">StillPhotographerNonCredited</momaf:orig>
    <momaf:orig name="elokreditoimatontekija" expl="A99">ProductionMember</momaf:orig>
    <momaf:orig name="elokreditoimatontekija" expl="B19">AssistantEditorNonCredited</momaf:orig>
    <momaf:orig name="elokreditoimatontekija" expl="D02">DirectorNonCredited</momaf:orig>
    <momaf:orig name="elokreditoimatontekija" expl="D03">ConductorNonCredited</momaf:orig>
    <momaf:orig name="elokreditoimatontekija" expl="D99">AssistantDirectorNonCredited</momaf:orig>
    <momaf:orig name="elokreditoimatontekija" expl="E03">ProductionMember</momaf:orig>
    <momaf:orig name="elokreditoimatontekija" expl="E05">ProductionMember</momaf:orig>
    <momaf:orig name="elokreditoimatontekija" expl="anm">AnimatorNonCredited</momaf:orig>
    <momaf:orig name="elokreditoimatontekija" expl="aud">DialogueNonCredited</momaf:orig>
    <momaf:orig name="elokreditoimatontekija" expl="aus">ScreenwriterNonCredited</momaf:orig>
    <momaf:orig name="elokreditoimatontekija" expl="chr">ChoreographerNonCredited</momaf:orig>
    <momaf:orig name="elokreditoimatontekija" expl="cmp">MusicNonCredited</momaf:orig>
    <momaf:orig name="elokreditoimatontekija" expl="cng">CinematographerNonCredited</momaf:orig>
    <momaf:orig name="elokreditoimatontekija" expl="cst">CostumedesignerNonCredited</momaf:orig>
    <momaf:orig name="elokreditoimatontekija" expl="exp">ExpertNonCredited</momaf:orig>
    <momaf:orig name="elokreditoimatontekija" expl="flm">EditorNonCreated</momaf:orig>
    <momaf:orig name="elokreditoimatontekija" expl="fmp">ProducerNonCredited</momaf:orig>
    <momaf:orig name="elokreditoimatontekija" expl="lgd">LightningdesignerNonCredited</momaf:orig>
    <momaf:orig name="elokreditoimatontekija" expl="mus">MusicianNonCredited</momaf:orig>
    <momaf:orig name="elokreditoimatontekija" expl="oth">ProductionMember</momaf:orig>
    <momaf:orig name="elokreditoimatontekija" expl="pmn">ProductionManagerNonCredited</momaf:orig>
    <momaf:orig name="elokreditoimatontekija" expl="rce">RecordistNonCredited</momaf:orig>
    <momaf:orig name="elokreditoimatontekija" expl="sds">SounddesignerNonCredited</momaf:orig>
    <momaf:orig name="elokreditoimatontekija" expl="std">SetdesignerNonCredited</momaf:orig>
    <momaf:orig name="elolaboratorio" expl="A99">Laboratory</momaf:orig>
    <momaf:orig name="elolevittaja" expl="fds">DistributorCompany</momaf:orig>
    <momaf:orig name="elonayttelija" expl="E01">Actor</momaf:orig>
    <momaf:orig name="elonayttelijakokoonpano" expl="A99">ActorGroup</momaf:orig>
    <momaf:orig name="elonayttelijakokoonpano" expl="oth">ActorGroup</momaf:orig>
    <momaf:orig name="eloosatuotantoyhtio" expl="E10">CoProductionCompany</momaf:orig>
    <momaf:orig name="elorahoitusyhtio" expl="fnd">FundingCompany</momaf:orig>
    <momaf:orig name="elotekija" expl="A08">Photographer</momaf:orig>
    <momaf:orig name="elotekija" expl="A12">ProductionMember</momaf:orig>
    <momaf:orig name="elotekija" expl="A13">StillPhotographer</momaf:orig>
    <momaf:orig name="elotekija" expl="A38">Originalwork</momaf:orig>
    <momaf:orig name="elotekija" expl="A43">ProductionMember</momaf:orig>
    <momaf:orig name="elotekija" expl="A99">ProductionMember</momaf:orig>
    <momaf:orig name="elotekija" expl="B01">Editor</momaf:orig>
    <momaf:orig name="elotekija" expl="B05">Adaptation</momaf:orig>
    <momaf:orig name="elotekija" expl="B06">ScriptTranslation</momaf:orig>
    <momaf:orig name="elotekija" expl="B13">Soundeditor</momaf:orig>
    <momaf:orig name="elotekija" expl="B19">AssistantEditor</momaf:orig>
    <momaf:orig name="elotekija" expl="B25">ProductionMember</momaf:orig>
    <momaf:orig name="elotekija" expl="D02">Director</momaf:orig>
    <momaf:orig name="elotekija" expl="D03">Conductor</momaf:orig>
    <momaf:orig name="elotekija" expl="D99">AssistantDirector</momaf:orig>
    <momaf:orig name="elotekija" expl="E02">ProductionMember</momaf:orig>
    <momaf:orig name="elotekija" expl="E03">ProductionMember</momaf:orig>
    <momaf:orig name="elotekija" expl="E05">ProductionMember</momaf:orig>
    <momaf:orig name="elotekija" expl="anm">Animator</momaf:orig>
    <momaf:orig name="elotekija" expl="aud">Dialogue</momaf:orig>
    <momaf:orig name="elotekija" expl="aus">Screenwriter</momaf:orig>
    <momaf:orig name="elotekija" expl="chr">Choreographer</momaf:orig>
    <momaf:orig name="elotekija" expl="cmm">ProductionMember</momaf:orig>
    <momaf:orig name="elotekija" expl="cmp">Music</momaf:orig>
    <momaf:orig name="elotekija" expl="cng">Cinematographer</momaf:orig>
    <momaf:orig name="elotekija" expl="cst">Costumedesigner</momaf:orig>
    <momaf:orig name="elotekija" expl="exp">Expert</momaf:orig>
    <momaf:orig name="elotekija" expl="fds">Distributor</momaf:orig>
    <momaf:orig name="elotekija" expl="flm">Editor</momaf:orig>
    <momaf:orig name="elotekija" expl="fmp">Producer</momaf:orig>
    <momaf:orig name="elotekija" expl="lgd">Lightningdesigner</momaf:orig>
    <momaf:orig name="elotekija" expl="mus">Musician</momaf:orig>
    <momaf:orig name="elotekija" expl="oth">ProductionMember</momaf:orig>
    <momaf:orig name="elotekija" expl="pmn">ProductionManager</momaf:orig>
    <momaf:orig name="elotekija" expl="rce">Recordist</momaf:orig>
    <momaf:orig name="elotekija" expl="sds">Sounddesigner</momaf:orig>
    <momaf:orig name="elotekija" expl="std">Setdesigner</momaf:orig>
    <momaf:orig name="elotekija" expl="trl">Translator</momaf:orig>
    <momaf:orig name="elotekijakokoonpano" expl="A99">ProductionMember</momaf:orig>
    <momaf:orig name="elotekijakokoonpano" expl="B05">AdaptationGroup</momaf:orig>
    <momaf:orig name="elotekijakokoonpano" expl="aus">ScreenwriterGroup</momaf:orig>
    <momaf:orig name="elotekijakokoonpano" expl="cmp">MusicGroup</momaf:orig>
    <momaf:orig name="elotekijakokoonpano" expl="cng">CinematographerGroup</momaf:orig>
    <momaf:orig name="elotekijakokoonpano" expl="cst">CostumedesignerGroup</momaf:orig>
    <momaf:orig name="elotekijakokoonpano" expl="mus">MusicianGroup</momaf:orig>
    <momaf:orig name="elotekijakokoonpano" expl="oth">ProductionMember</momaf:orig>
    <momaf:orig name="elotekijakokoonpano" expl="std">SetdesignerGroup</momaf:orig>
    <momaf:orig name="elotekijayhtio" expl="A99">ProductionMember</momaf:orig>
    <momaf:orig name="elotekijayhtio" expl="anm">AnimationCompany</momaf:orig>
    <momaf:orig name="elotekijayhtio" expl="cmp">MusicCompany</momaf:orig>
    <momaf:orig name="elotekijayhtio" expl="cng">CinematographerCompany</momaf:orig>
    <momaf:orig name="elotekijayhtio" expl="oth">ProductionMember</momaf:orig>
    <momaf:orig name="elotekijayhtio" expl="std">SetdesignerCompany</momaf:orig>
    <momaf:orig name="elotilaaja" expl="A99">ProductionMember</momaf:orig>
    <momaf:orig name="elotuotantoyhtio" expl="E10">ProductionCompany</momaf:orig>
    <momaf:orig name="muutesiintyjat" expl="E99">OtherPerformer</momaf:orig>
    <momaf:orig name="muuttekijat" expl="oth">ProductionMember</momaf:orig>
  </xsl:variable>

  <!-- Mapping from filming location terms to MoMaF filming location classes -->
  <xsl:variable name="locmap">
    <momaf:orig key="elokuva_ulkokuvat">Outdoorlocation</momaf:orig>
    <momaf:orig key="elokuva_sisakuvat">Indoorlocation</momaf:orig>
    <momaf:orig key="elokuva_studiot">Studiolocation</momaf:orig>
  </xsl:variable>

  <!-- Mapping from Elonet agenty types to MoMaF agent classes -->
  <xsl:variable name="agenttypemap">
    <momaf:orig key="elonet_elokuva">Movie</momaf:orig>
    <momaf:orig key="elonet_henkilo">Person</momaf:orig>
    <momaf:orig key="elonet_yhtio">Company</momaf:orig>
    <momaf:orig key="elonet_kokoonpano">Group</momaf:orig>
    <momaf:orig key="">Unknown</momaf:orig>
  </xsl:variable>

  <!-- Mapping from Elonet rating process terms to MoMaF ontology properties -->
  <xsl:variable name="classificationmap">
    <momaf:orig key="elokuva-tarkastus-formaatti">classificationFormat</momaf:orig>
    <momaf:orig key="elokuva-tarkastus-ikaraja">classificationRating</momaf:orig>
    <momaf:orig key="elokuva-tarkastus-osalkm">classificationAmountOfParts</momaf:orig>
    <momaf:orig key="elokuva-tarkastus-pituus">classificationLength</momaf:orig>
    <momaf:orig key="elokuva-tarkastus-tarkastuselin">classificationAgency</momaf:orig>
    <momaf:orig key="elokuva-tarkastus-tarkastusilmoitus">classificatioNotification</momaf:orig>
    <momaf:orig key="elokuva-tarkastus-tarkastusnro">classificationNumber</momaf:orig>
    <momaf:orig key="elokuva-tarkastus-veroluokka">classificationTaxCategory</momaf:orig>
    <momaf:orig key="elokuva-tarkastus-kesto">classificationDuration</momaf:orig>
    <momaf:orig key="elokuva-tarkastus-tarkastuttaja">classificationInstigator</momaf:orig>
    <momaf:orig key="elokuva-tarkastus-leikattumetria">classificationCensoredMeters</momaf:orig>
    <momaf:orig key="elokuva-tarkastus-perustelut">classificationExplanation</momaf:orig>
    <momaf:orig key="elokuva-tarkastus-tarkastamolaji">classicationClasserType</momaf:orig>
    <momaf:orig key="elokuva-tarkastus-luokittelu-sisalto">classificationClassContent</momaf:orig>
    <momaf:orig key="elokuva-tarkastus-tarkastusaihe">classificationSubject</momaf:orig>
    <momaf:orig key="elokuva-tarkastus-muuttiedot">classificationOtherInfo</momaf:orig>
    <momaf:orig key="elokuva-tarkastus-kuvakoko">classificationScreenSize</momaf:orig>
    <momaf:orig key="elokuva-tarkastus-suositusika">classificationAgeRecommendation</momaf:orig>
    <momaf:orig key="elokuva-tarkastus-leikattuaikaa">classificationCensoredDuration</momaf:orig>
    <momaf:orig key="elokuva-tarkastus-luokittelu-luokittelun_tilaaja">classificationOrderedBy</momaf:orig>
  </xsl:variable>

  <!-- Function to parse the Elonet date format and return it as XSD compatible -->
  <xsl:function name="momaf:parsedate">
    <xsl:param name="ds" as="xs:string"/>
    <xsl:choose>
      <xsl:when test="$ds='00.00.0000'"/>
      <xsl:otherwise>
	<momaf:date rdf:datatype="xs:date"><xsl:value-of select="replace(string-join(reverse(tokenize($ds,'\.')),'-'),'-00','-01')"/></momaf:date>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:function>

  <xsl:function name="momaf:parselength">
    <xsl:param name="ds" as="xs:string"/>
    <xsl:variable name="as" select="replace($ds,' ','')"/>
    <xsl:analyze-string select="$as" regex="^([0-9]+)m$">
      <xsl:matching-substring>
	<momaf:length>
	  <xsl:value-of select="regex-group(1)"/>
	</momaf:length>
      </xsl:matching-substring>
      <xsl:non-matching-substring>
	<xsl:analyze-string select="$as" regex="^([0-9]+)min">
	  <xsl:matching-substring>
	    <momaf:duration rdf:datatype="xs:duration">PT<xsl:value-of select="regex-group(1)"/>M</momaf:duration>
	  </xsl:matching-substring>
	  <xsl:non-matching-substring>
	    <xsl:analyze-string select="$as" regex="\D(\d?\d):(\d?\d):(\d?\d)\D">
	      <xsl:matching-substring>
		<momaf:duration rdf:datatype="xs:duration">PT<xsl:value-of select="regex-group(1)"/>H<xsl:value-of select="regex-group(2)"/>M<xsl:value-of select="regex-group(3)"/>S</momaf:duration>
	      </xsl:matching-substring>
	      <xsl:non-matching-substring>
		<xsl:analyze-string select="$as" regex="(\d+)'(\d*)">
		  <xsl:matching-substring>
		    <momaf:duration rdf:datatype="xs:duration">PT<xsl:value-of select="regex-group(1)"/>M<xsl:value-of select="regex-group(2)"/>S</momaf:duration>
		  </xsl:matching-substring>
		</xsl:analyze-string>
	      </xsl:non-matching-substring>
	    </xsl:analyze-string>
	  </xsl:non-matching-substring>
	</xsl:analyze-string>
      </xsl:non-matching-substring>
    </xsl:analyze-string>
  </xsl:function>

  <xsl:function name="momaf:get_first_int">
    <xsl:param name="ds" as="xs:string"/>
    <xsl:analyze-string select="replace($ds,' ','')" regex="^\D*(\d+)">
      <xsl:matching-substring><xsl:value-of select="regex-group(1)"/></xsl:matching-substring>
    </xsl:analyze-string>
  </xsl:function>

  <!-- The Elonet data has three different types of Cinematographic
       Work entries: Movies, Images, and Videos. Images and Videos are
       extracts from the movies. These three classes have a common
       superclass Media.

The next three templates create the actual Media nodes, the name of
which is given in rdf:resource attribute of rdf:Description. All
consequent data resulting from the descending applications of
xsl:apply-templates therefore has the subject already defined and only
need to define the ver and object.
 -->
  
  <!-- Main template for Movie node -->
  <xsl:template match="CinematographicWork[Identifier[@IDTypeName='elonet_elokuva']]">
    <rdf:Description rdf:about="http://momaf-data.utu.fi/elonet_elokuva_{Identifier}">
      <rdf:type rdf:resource="http://momaf-data.utu.fi/Movie"/>
      <momaf:elonet_movie_ID><xsl:value-of select="Identifier"/></momaf:elonet_movie_ID>
      <xsl:apply-templates>
	<xsl:with-param name="elonet_id" select="Identifier" tunnel="yes"/>
      </xsl:apply-templates>	
    </rdf:Description>
  </xsl:template>

  <!-- Main template for Image node -->
  <xsl:template match="CinematographicWork[Identifier[@IDTypeName='elonet_materiaali_kuva']]">
    <rdf:Description rdf:about="http://momaf-data.utu.fi/{Identifier/@IDTypeName}_{Identifier}">
      <rdf:type rdf:resource="http://momaf-data.utu.fi/Image"/>
      <xsl:apply-templates/>
      <momaf:sourcefile><xsl:value-of select="ProductionEvent/ProductionEventType/@elokuva-elonet-materiaali-kuva-url"/></momaf:sourcefile>
    </rdf:Description>
  </xsl:template>

  <!-- Main template for Video node -->
  <xsl:template match="CinematographicWork[Identifier[@IDTypeName='elonet_materiaali_video']]">
    <rdf:Description rdf:about="http://momaf-data.utu.fi/{Identifier/@IDTypeName}_{Identifier}">
      <rdf:type rdf:resource="http://momaf-data.utu.fi/Video"/>
      <xsl:apply-templates/>
      <momaf:sourcefile><xsl:value-of select="ProductionEvent/ProductionEventType/@elokuva-elonet-materiaali-video-url"/></momaf:sourcefile>
    </rdf:Description>
  </xsl:template>

  <!-- Various ID fields. This is not good, results are not unique in
       case of Images. -->
  <xsl:template match="Identifier[@scheme='KAVI']">
    <xsl:choose>
      <xsl:when test="@IDTypeName!=''">
	<momaf:elonet_ID>
	  <xsl:value-of select="@IDTypeName"/>_<xsl:value-of select="."/>
	</momaf:elonet_ID>
      </xsl:when>
      <xsl:otherwise>
	<momaf:identifier>
	  <xsl:value-of select="."/>
	</momaf:identifier>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <!-- Simple translations of various field- -->
  <xsl:template match="RecordSource">
      <momaf:recordSource><xsl:value-of select="SourceName"/></momaf:recordSource>
  </xsl:template>
  <xsl:template match="IdentifyingTitle">
    <skos:prefLabel><xsl:apply-templates/></skos:prefLabel>
  </xsl:template>
  <xsl:template match="Title[TitleRelationship[.='original']]">
    <rdfs:label><xsl:value-of select="TitleText"/></rdfs:label>
  </xsl:template>
  <xsl:template match="Title[TitleRelationship[.=('alternative','working','unspecified','other')]]">
    <rdfs:label><xsl:value-of select="TitleText"/></rdfs:label>
  </xsl:template>
  <xsl:template match="Title[TitleRelationship[.='translated']]">
    <xsl:variable name="val"><xsl:value-of select="TitleText/@lang"/></xsl:variable>
    <rdfs:label xml:lang="{$langmap/momaf:orig[@key=$val]/.}"><xsl:value-of select="TitleText"/></rdfs:label>
  </xsl:template>
  <xsl:template match="CountryOfReference">
    <momaf:productioncountry><xsl:value-of select="Country/RegionName"/></momaf:productioncountry>
  </xsl:template>
  <xsl:template match="YearOfReference">
    <momaf:productionyear><xsl:apply-templates/></momaf:productionyear>
  </xsl:template>
  <!-- Agent in Elonet is anyone that is documented in relation with a
       Media.

In MoMaF ontology, the Agent is a superclass for classes Person,
Group, and Company. These are legal entities that have identity and
name. Each Person, Groups or Company is supposed to exist in the data
base only once.

Elonet links these Agents directly with Media. In RDF this is not
possible without losing annotative capabilities, so an intermediate
class has been created: ProductionMember, that has several more
specific subclasses.

Each Media is a node; also each Agent is a node. In MoMaF ontology,
the participation of an Agent in a Media is also a node of any of the
subclasses of ProductionMember.

The data recorded therefore is the participation of an Agent in a
Media. This participation can have additional information, like
detailed work and role descriptions.

This template is the main template for parsing a participation of an
Agent in a Media.
  -->
  <xsl:template match="HasAgent">
    <!-- Gather various data to temporary variables -->
    <xsl:variable name="agtype"><xsl:value-of select="AgentIdentifier/IDTypeName"/></xsl:variable>
    <xsl:variable name="agid"><xsl:value-of select="$agtype"/>_<xsl:value-of select="AgentIdentifier/IDValue"/></xsl:variable>
    <xsl:variable name="elonet-tag"><xsl:value-of select="@elonet-tag/data()"/></xsl:variable>
    <xsl:variable name="activity-code" select="Activity/text()"/>
    <xsl:variable name="agentclass"><xsl:value-of select="$agentmap/momaf:orig[@name=$elonet-tag and @expl=$activity-code]"/></xsl:variable>
    <xsl:variable name="agenttype"><xsl:value-of select="$agenttypemap/momaf:orig[@key=$agtype]"/></xsl:variable>
    <!-- Add verb momaf:hasMember to the subject defined in main Media
         template above. -->
    <momaf:hasMember>
      <!-- Add anonymous membership node -->
      <rdf:Description>
	<!-- the type of the node = the position in production -->
	<rdf:type rdf:resource="http://momaf-data.utu.fi/{$agentclass}"/>
	<!-- link the Agent to the membership using momaf:hasAgent -->
	<momaf:hasAgent>
	  <!-- Agent node. There will be duplicates, but since this is
	       a named node (see rdf:about), the duplicate statements
	       will always refer to same node and there will be no
	       duplicates in the triple store. -->
	  <rdf:Description rdf:about="http://momaf-data.utu.fi/{$agid}">
	    <rdf:type rdf:resource="http://momaf-data.utu.fi/{$agenttype}"/>
	    <momaf:elonet_ID><xsl:value-of select="$agid"/></momaf:elonet_ID>
	    <xsl:if test="$agtype='elonet_henkilo'">
	      <momaf:elonet_person_ID><xsl:value-of select="AgentIdentifier/IDValue/text()"/></momaf:elonet_person_ID>
	    </xsl:if>
	    <xsl:if test="$agtype='elonet_yhtio'">
	      <momaf:elonet_corporate_ID><xsl:value-of select="AgentIdentifier/IDValue/text()"/></momaf:elonet_corporate_ID>
	    </xsl:if>
	    <xsl:if test="$agtype='elonet_kokoonpano'">
	      <momaf:elonet_group_ID><xsl:value-of select="AgentIdentifier/IDValue/text()"/></momaf:elonet_group_ID>
	    </xsl:if>
	    <xsl:if test="not(empty(@elonet-tag))">
	      <rdfs:label><xsl:value-of select="normalize-unicode(AgentName)"/></rdfs:label>
	      <skos:prefLabel><xsl:value-of select="normalize-unicode(AgentName)"/></skos:prefLabel>
	    </xsl:if>
	  </rdf:Description>
	</momaf:hasAgent>
	<!-- add work/role description from membership -->
	<xsl:if test="Activity/@tehtava!=''">
	  <momaf:workDescription><xsl:value-of select="Activity/@tehtava"/></momaf:workDescription>
	</xsl:if>
	<xsl:if test="AgentName/@elokuva-elonayttelija-rooli!=''">
	  <momaf:roleDescription><xsl:value-of select="AgentName/@elokuva-elonayttelija-rooli"/></momaf:roleDescription>
	</xsl:if>
      </rdf:Description>
    </momaf:hasMember>
  </xsl:template>

  <!-- TV broadcast. Named node so a particular broadcast can be
       referred to. -->
  <xsl:template match="ProductionEvent[@elonet-tag='elotelevisioesitys']">
    <xsl:param name="elonet_id" tunnel="yes"/>
    <xsl:variable name="brid"><xsl:value-of select="$elonet_id"/>_<xsl:value-of select="ProductionEventType/@elokuva-elotelevisioesitys-esitysaika"/>_<xsl:value-of select="ProductionEventType/@elokuva-elotelevisioesitys-paikka"/></xsl:variable>
    <momaf:hasBroadcast>
      <rdf:Description rdf:about="http://momaf-data.utu.fi/broadcast#{encode-for-uri($brid)}">
	<rdf:type rdf:resource="http://momaf-data.utu.fi/Broadcast"/>
	<xsl:apply-templates/>
      </rdf:Description>
    </momaf:hasBroadcast>
  </xsl:template>
  <!-- These three gets called from within the template above -->
  <xsl:template match="ProductionEventType[.='BRO']/@elokuva-elotelevisioesitys-esitysaika">
    <xsl:copy-of select="momaf:parsedate(.)"/>
  </xsl:template>
  
  <xsl:template match="ProductionEventType[.='BRO']/@elokuva-elotelevisioesitys-paikka">
    <momaf:broadcastplace><xsl:value-of select="."/></momaf:broadcastplace>
  </xsl:template>
  <xsl:template match="ProductionEventType[.='BRO']/@elokuva-elotelevisioesitys-katsojamaara">
    <momaf:audience><xsl:value-of select="momaf:get_first_int(.)"/></momaf:audience>
  </xsl:template>
  
  
  <xsl:template match="ProductionEventType[.='BRO']">
    <xsl:apply-templates select="@*"/>
  </xsl:template>
  
  <!-- Ratings. Contains technical data related to the actual version rated. -->
  <xsl:template match="ProductionEvent[@elonet-tag='tarkastus']">
    <xsl:param name="elonet_id" tunnel="yes"/>
    <momaf:hasClassification>
      <xsl:variable name="classificationid"><xsl:value-of select="$elonet_id"/>_<xsl:value-of select="momaf:parsedate(DateText/text())"/>_<xsl:value-of select="ProductionEventType/@elokuva-tarkastus-formaatti"/></xsl:variable>
      <rdf:Description rdf:about="http://momaf-data.utu.fi/classification#{encode-for-uri($classificationid)}">
	<rdf:type rdf:resource="http://momaf-data.utu.fi/Classification"/>
	<xsl:apply-templates select="node()|node()/@*"/>
      </rdf:Description>
    </momaf:hasClassification>
  </xsl:template>
  <!-- Specific conversions for classification data -->
  <xsl:template match="ProductionEventType[.='CEN']/@elokuva-tarkastus-pituus|@elokuva-tarkastus-kesto" priority="2">
    <xsl:copy-of select="momaf:parselength(.)"/>
  </xsl:template>
  <!-- Convert various rating data to properties. See classification
       map above. This is the generic conversion. -->
  <xsl:template match="ProductionEventType[.='CEN']/@*">
    <xsl:variable name="type" select="name(.)"/>
    <xsl:variable name="restype" select="$classificationmap/momaf:orig[@key=$type]"/>
    <xsl:element name="momaf:{$restype}"><xsl:value-of select="."/></xsl:element>
  </xsl:template>
  <xsl:template match="ProductionEventType[.='CEN']"/>

  <!-- Convert Elonet date field. 

TODO This gets called in places it is not needed. -->
  <xsl:template match="DateText">
    <xsl:copy-of select="momaf:parsedate(.)"/>
  </xsl:template>

  <!-- Presentation of the Movie at a festival -->
  <xsl:template match="ProductionEvent[@elonet-tag='elofestivaaliosallistuminen']">
    <momaf:moviefestival rdf:parseType="Resource">
      <rdfs:label><xsl:value-of select="ProductionEventType/@elokuva-elokuvafestivaaliosallistuminen-aihe"/></rdfs:label>
      <momaf:date rdf:datatype="xs:gYear"><xsl:value-of select="momaf:get_first_int(DateText)"/></momaf:date>
    </momaf:moviefestival>
  </xsl:template>

  <!-- Empty templates to ignore subfields of ProductionEvent 

In many cases, these produce extra text that has no actual information
content.-->
  <xsl:template match="ProductionEvent[@elonet-tag='ensiesityspaiva']"/>
  <xsl:template match="ProductionEvent[@elonet-tag=('ensiesityspaiva','ensiesityspaikat','eloulkomaanmyynti','muuesitys','kutsuvierasnäytäntö','teatterikopioidenlkm','ulkokuvat','sisakuvat','studiot','yhteistyokumppanit','kuvauspaikkahuomautus')]/ProductionEventType"/>
  <xsl:template match="ProductionEvent[@elonet-tag=('ensiesityspaiva','ensiesityspaikat','eloulkomaanmyynti','muuesitys','teatterikopioidenlkm','ulkokuvat','sisakuvat','studiot','yhteistyokumppanit','kuvauspaikkahuomautus')]/ProductionEventType" mode="fulldesc" />

  <!-- Premieres -->
  <xsl:template match="ProductionEvent[@elonet-tag='ensiesityspaikat']">
    <xsl:apply-templates>
      <xsl:with-param name="scrdate" tunnel="yes" select="../ProductionEvent[@elonet-tag='ensiesityspaiva']/DateText"/>
      <xsl:with-param name="scrtype" tunnel="yes">http://momaf-data.utu.fi/Premiere</xsl:with-param>
    </xsl:apply-templates>
  </xsl:template>

  <!-- Other screenings -->
  <xsl:template match="ProductionEvent[@elonet-tag='muuesitys']">
    <xsl:apply-templates>
      <xsl:with-param name="scrdate" tunnel="yes" select="DateText"/>
      <xsl:with-param name="scrtype" tunnel="yes">http://momaf-data.utu.fi/Screening</xsl:with-param>
    </xsl:apply-templates>
  </xsl:template>

  <!-- Private screenings-->
  <xsl:template match="ProductionEvent[@elonet-tag='kutsuvierasnäytäntö']">
    <xsl:apply-templates>
      <xsl:with-param name="scrdate" tunnel="yes" select="DateText"/>
      <xsl:with-param name="scrtype" tunnel="yes">http://momaf-data.utu.fi/ScreeningPrivate</xsl:with-param>
    </xsl:apply-templates>
  </xsl:template>

  <xsl:template match="Region">
    <xsl:apply-templates/>
  </xsl:template>
  <!-- Parse location data for screening (premiere, other) resulting
       in Movie Theatre data.

The following matches the RegionName elements only in certain context,
because the RegionName field is parsed for administrative location
names and movie theatres. In some other place the RegionName could
mean something else.
-->
  <xsl:template match="RegionName[../../ProductionEventType/text()=('PRE','SCR')]">
    <xsl:param name="elonet_id" tunnel="yes"/>
    <xsl:param name="scrdate" tunnel="yes"/>
    <xsl:param name="scrtype" tunnel="yes"/>
    <xsl:for-each select="tokenize(.,'; *')">
      <xsl:analyze-string select="." regex="^(.*): (.*)$">
	<xsl:matching-substring>
	  <xsl:variable name="city"><xsl:value-of select="regex-group(1)"/></xsl:variable>
	  <xsl:for-each select="tokenize(regex-group(2),', *')">
	    <!-- Link a screening with the movie -->
	    <momaf:hasScreening>
	      <xsl:variable name="scrname"><xsl:value-of
	      select="$elonet_id"/>_scr_<xsl:value-of
	      select="$city"/>_<xsl:value-of
	      select="."/>_<xsl:value-of
	      select="$scrdate"/></xsl:variable>
	      <!-- Create the screening as named node. Individual
	           screenings can be searched for.-->
	      <rdf:Description rdf:about="http://momaf-data.utu.fi/{encode-for-uri($scrname)}">
		<rdf:type rdf:resource="{$scrtype}"/>
		<xsl:apply-templates select="$scrdate"/>
		<momaf:atTheatre>
		  <!-- Add node for theatre as named node. Individual
		       theaters can be analyzed. -->
		  <xsl:variable name="theatreid"><xsl:value-of select="."/>_<xsl:value-of select="$city"/></xsl:variable>
		  <rdf:Description rdf:about="http://momaf-data.utu.fi/theatre#{encode-for-uri($theatreid)}">
		    <rdf:type rdf:resource="http://momaf-data.utu.fi/Theatre"/>
		    <rdfs:label><xsl:value-of select="."/></rdfs:label>
		    <momaf:hasAdminplace rdf:resource="http://momaf-data.utu.fi/adminplace#{encode-for-uri($city)}"/>
		  </rdf:Description>
		</momaf:atTheatre>
	      </rdf:Description>
	    </momaf:hasScreening>
	  </xsl:for-each>
	</xsl:matching-substring>
	<xsl:non-matching-substring/>
      </xsl:analyze-string>
    </xsl:for-each>
  </xsl:template>

  <!-- Exported to country -->
  <xsl:template match="ProductionEvent[@elonet-tag='eloulkomaanmyynti']">
      <momaf:export><xsl:apply-templates/></momaf:export>
  </xsl:template>

  <!-- Number of film copies -->
  <xsl:template match="ProductionEvent[@elonet-tag='teatterikopioidenlkm']">
    <momaf:copiesamount><xsl:value-of select="ProductionEventType/@elokuva-teatterikopioidenlkm"/></momaf:copiesamount>
  </xsl:template>

  <!-- Audience in theatres -->
  <xsl:template match="ProductionEvent[@elonet-tag='katsojaluku']/ProductionEventType">
    <momaf:audience rdf:datatype="xs:int"><xsl:value-of select="momaf:get_first_int(replace(@elokuva-katsojaluku,' ',''))"/></momaf:audience>
    <momaf:audienceNote><xsl:value-of select="@elokuva-katsojaluku"/></momaf:audienceNote>
  </xsl:template>

  <!-- Box office earnings

TODO This could improved so that it parses the number and the currency
from the text. -->
  <xsl:template match="ProductionEvent[@elonet-tag='lipputulot']/ProductionEventType">
    <momaf:income><xsl:value-of select="@elokuva-lipputulot"/></momaf:income>
  </xsl:template>

  <!-- Elonet subject terms. Created as named nodes. -->
  <xsl:template match="SubjectTerms/Term">
    <momaf:hasKeyword>
      <rdf:Description rdf:about="http://momaf-data.utu.fi/subject/{encode-for-uri(.)}">
	<rdf:type rdf:resource="http://momaf-data.utu.fi/Subject"/> 
	<rdfs:label xml:lang="fi"><xsl:value-of select="."/></rdfs:label>
	<skos:prefLabel xml:lang="fi"><xsl:value-of select="."/></skos:prefLabel>
      </rdf:Description>
    </momaf:hasKeyword>
  </xsl:template>

  <!-- Awards won -->
  <xsl:template match="Award">
    <momaf:award><xsl:apply-templates/></momaf:award>
  </xsl:template>

  <!-- Original subject for film from/by -->
  <xsl:template match="ProductionEvent[@elonet-tag='alkuperaisaihe']/ProductionEventType">
    <momaf:originalidea><xsl:value-of select="normalize-unicode(@elokuva-alkuperaisaihe)"/></momaf:originalidea>
  </xsl:template>

  <!-- Original work, if adaptation -->
  <xsl:template match="ProductionEvent[@elonet-tag='alkuperaisteos']/ProductionEventType">
    <momaf:originalwork><xsl:value-of select="normalize-unicode(@elokuva-alkuperaisteos)"/></momaf:originalwork>
  </xsl:template>

  <!-- Music. Freetext

TODO This could be improved by parsing the string for more details. -->
  <xsl:template match="ProductionEvent[@elonet-tag='musiikki']">
    <momaf:music rdf:datatype="rdf:HTML"><xsl:apply-templates select="elokuva_musiikki"/></momaf:music>
  </xsl:template>

  <!-- Film type -->
  <xsl:template match="ProductionEvent[@elonet-tag='laji2fin']">
    <xsl:for-each select="tokenize(elokuva_laji2fin,',')">
      <momaf:hasMovietype>
	<rdf:Description rdf:about="http://momaf-data.utu.fi/movietype/{encode-for-uri(normalize-space(.))}">
	  <rdf:type rdf:resource="http://momaf-data.utu.fi/Movietype"/>
	  <rdfs:label xml:lang="fi"><xsl:value-of select="normalize-space(.)"/></rdfs:label>
	</rdf:Description>
      </momaf:hasMovietype>
    </xsl:for-each>
  </xsl:template>

  <!-- Genre. Vocabulary as named nodes. -->
  <xsl:template match="ProductionEvent[@elonet-tag='genre']">
    <momaf:hasGenre>
      <rdf:Description rdf:about="http://momaf-data.utu.fi/genre/{encode-for-uri(ProductionEventType/@elokuva-genre)}">
	<rdf:type rdf:resource="http://momaf-data.utu.fi/Genre"/>
	<rdfs:label xml:lang="fi"><xsl:value-of select="ProductionEventType/@elokuva-genre"/></rdfs:label>
      </rdf:Description>
    </momaf:hasGenre>
  </xsl:template>

  <!-- National Filmography ID. From printed filmography? -->
  <xsl:template match="ProductionEvent[@elonet-tag='skftunniste']">
    <momaf:skfid><xsl:value-of select="ProductionEventType/@elokuva-skftunniste"/></momaf:skfid>
  </xsl:template>

  <!-- Main template for parsing filming locations. 

The locations are parsed two times. First time parses each location
description for town, location and scene. Second time includes the
whole filming location description as it is.
-->
  <xsl:template match="ProductionEvent[@elonet-tag=('sisakuvat','ulkokuvat','studiot')]">
    <xsl:apply-templates/>
    <xsl:apply-templates mode="fulldesc"/>
  </xsl:template>
  <!-- This is the first parsin of filming locations.

This tries really hard to find sensible place names and scene locations from the data.
-->
  <xsl:template match="elokuva_ulkokuvat|elokuva_sisakuvat|elokuva_studiot">
    <xsl:variable name="ins"><xsl:value-of select="replace(replace(.,'&amp;','&amp;amp;'),'I&gt;','i&gt;')"/></xsl:variable>
    <xsl:variable name="tp" select="name()"/>
    <xsl:variable name="elname">http://momaf-data.utu.fi/<xsl:value-of
    select="$locmap/momaf:orig[@key=$tp]"/></xsl:variable>
    <!-- In the data, filming locations are separated by <br/> elements. -->
    <xsl:for-each-group select="parse-xml-fragment($ins)/node()" group-adjacent="not(name()='br')" >
	<xsl:variable name="adplace">
	  <xsl:apply-templates select="current-group()" mode="adplace"/>
	</xsl:variable>
	<xsl:for-each-group select="current-group()" group-starting-with="node()[matches(.,'\)')]">
	  <xsl:variable name="locrow">
	    <xsl:apply-templates select="current-group()" mode="scenes"/>
	  </xsl:variable>
	  <xsl:for-each select="$locrow/momaf:scenelocation">
	    <momaf:hasFilmingLocation>
	      <rdf:Description>
		<rdf:type rdf:resource="{$elname}"/>
		<xsl:copy-of select="$adplace/momaf:hasAdminplace"/><xsl:copy-of select="$locrow/momaf:localname"/><xsl:copy-of select="."/>
	      </rdf:Description>
	    </momaf:hasFilmingLocation>
	  </xsl:for-each>
	</xsl:for-each-group>
    </xsl:for-each-group>
  </xsl:template>
  <!-- This is the second parsing of filming locations. 
  -->
  <xsl:template match="elokuva_ulkokuvat|elokuva_sisakuvat|elokuva_studiot" mode="fulldesc">
    <xsl:variable name="tp" select="name()"/>
    <xsl:variable name="elname">http://momaf-data.utu.fi/<xsl:value-of select="$locmap/momaf:orig[@key=$tp]"/></xsl:variable>
    <xsl:variable name="ins2"><xsl:copy-of select="."/></xsl:variable>
    <xsl:variable name="elnamefulldesc"><xsl:value-of select="$elname"/>Fulldescription</xsl:variable>
    <momaf:hasFilmingLocationFullDescription>
      <rdf:Description>
	<rdf:type rdf:resource="{$elnamefulldesc}"/>
	<rdfs:comment xml:lang="fi" rdf:datatype="rdf:HTML">
	  <xsl:value-of select="$ins2"/>
	</rdfs:comment>
      </rdf:Description>
    </momaf:hasFilmingLocationFullDescription>
  </xsl:template>
  <!-- "adminplace" in this terminology refers to an administrative
       name of a place: a town, city, country, etc. -->
  <xsl:template match="/node()[matches(.,'^.*: .*$')]" mode="adplace">
    <xsl:analyze-string select="." regex="^(.*): ">
      <xsl:matching-substring>
	<momaf:hasAdminplace>
	  <rdf:Description rdf:about="http://momaf-data.utu.fi/adminplace#{encode-for-uri(regex-group(1))}">
	    <rdf:type rdf:resource="http://momaf-data.utu.fi/Adminplace"/>
	    <rdfs:label xml:lang="fi"><xsl:value-of select="regex-group(1)"/></rdfs:label>
	    <skos:prefLabel><xsl:value-of select="regex-group(1)"/></skos:prefLabel>
	  </rdf:Description>
	</momaf:hasAdminplace>
      </xsl:matching-substring>
      <xsl:non-matching-substring/>
    </xsl:analyze-string>
  </xsl:template>
  <!-- Parsing of scene locations -->
  <xsl:template match="/node()[matches(.,'[,:^] (.*) \(')]" mode="scenes">
    <xsl:analyze-string select="." regex="[,:^] (.*) \(">
      <xsl:matching-substring>
	<momaf:localname><xsl:value-of select="regex-group(1)"/></momaf:localname>
      </xsl:matching-substring>
      <xsl:non-matching-substring/>
    </xsl:analyze-string>
  </xsl:template>
  <xsl:template match="*" mode="l2"/>
  <xsl:template match="i|I" mode="scenes">
    <xsl:for-each select="tokenize(.,',')">
      <momaf:scenelocation><xsl:value-of select="normalize-space(.)"/></momaf:scenelocation>
    </xsl:for-each>
  </xsl:template>

  <!-- Remove line breaks. -->
  <xsl:template match="/br">
  </xsl:template>
  <!--xsl:template match="/i[count(following-sibling::br)>0]">
    <momaf:scenelocation><xsl:value-of select="."/></momaf:scenelocation>
  </xsl:template-->

  <!--xsl:template match="/node()[matches(.,'^.*: .*$')]" mode="locations">
    <xsl:analyze-string select="." regex="^(.*): (.*)$">
      <xsl:matching-substring>
	<xsl:variable name="ml"><xsl:value-of select="normalize-space(regex-group(1))"/></xsl:variable>
	<xsl:for-each select="tokenize(regex-group(2),',')">
	  <momaf:locationdata>
	    <momaf:adminplace>
	      <rdf:Description rdf:about="momafadminplace:{encode-for-uri($ml)}">
		<rdf:label><xsl:value-of select="$ml"/></rdf:label>
	      </rdf:Description>
	    </momaf:adminplace>
	    <momaf:localname><xsl:apply-templates select="normalize-space(.)"/></momaf:localname>
	  </momaf:locationdata>
	</xsl:for-each>
      </xsl:matching-substring>
    </xsl:analyze-string>
    </xsl:template-->
  <!-- Try to match the information source in the filming locations.

TODO this does  not work .-->
  <xsl:template match="/node()[starts-with(.,'-')]" mode="locations" priority="1">
    <momaf:sourcedata><momaf:sourcedesc><xsl:apply-templates/></momaf:sourcedesc></momaf:sourcedata>
  </xsl:template>
  <!-- Skip the KAVI information gathering data

This field contains requests for information aimed at the public using
Elonet data. -->
  <xsl:template match="ProductionEvent[@elonet-tag=('tiedonkeruu','elotiedonkeruu')]"/>
  <!-- Various technical data -->
  <xsl:template match="ProductionEvent/ProductionEventType[.='MISC']/@elokuva-alkupkesto|@elokuva-alkuppituus">
    <xsl:copy-of select="momaf:parselength(.)"/>
  </xsl:template>
  <xsl:template match="ProductionEvent/ProductionEventType[.='MISC']">
    <xsl:apply-templates select="@elokuva-alkupkesto|@elokuva-alkuppituus"/>
    <momaf:soundsystem><xsl:value-of select="@elokuva-alkupaanijarjestelma"/></momaf:soundsystem>
    <momaf:color><xsl:value-of select="@elokuva-alkupvari"/></momaf:color>
    <momaf:aspectratio><xsl:value-of select="@elokuva-kuvasuhde"/></momaf:aspectratio>
  </xsl:template>

  <!-- The use rights of tthe images and videos is confusingly documented.

TODO Check if this is really so. -->
  <xsl:template match="ProductionEventType[@elokuva-elonet-materiaali-kuva-url!='' or @elokuva-elonet-materiaali-video-url!='']">
    <momaf:rights><xsl:value-of select="@finna-kayttooikeus"/></momaf:rights>
  </xsl:template>

  <!-- Comments on filming locations. -->
  <xsl:template match="ProductionEvent[@elonet-tag='kuvauspaikkahuomautus']/elokuva_kuvauspaikkahuomautus">
    <momaf:locationcomment><xsl:apply-templates/></momaf:locationcomment>
  </xsl:template>

  <!-- Co-operation in film production ? -->
  <xsl:template match="ProductionEvent[@elonet-tag='yhteistyokumppanit']/elokuva_yhteistyokumppanit">
    <momaf:cooperation><xsl:apply-templates/></momaf:cooperation>
  </xsl:template>

  <!-- Review samples -->
  <xsl:template match="ProductionEvent[@elonet-tag='lehdistoarvio']">
    <momaf:hasReview rdf:datatype="rdf:HTML">
      <xsl:apply-templates select="elokuva_lehdistoarvio"/>
    </momaf:hasReview>
  </xsl:template>

  <!-- Commentary -->
  <xsl:template match="ProductionEvent[@elonet-tag='huomautukset']">
    <momaf:hasCommentary rdf:datatype="rdf:HTML">
      <xsl:apply-templates select="elokuva_huomautukset"/>
    </momaf:hasCommentary>
  </xsl:template>

  <!-- Synopsis -->
  <xsl:template match="ContentDescription[DescriptionType='Synopsis']">
    <momaf:hasSynopsis rdf:datatype="rdf:HTML">
      <xsl:attribute name="xml:lang"><xsl:apply-templates select="Language"/></xsl:attribute>
      <xsl:value-of select="DescriptionText"/>
    </momaf:hasSynopsis>
  </xsl:template>

  <!-- Content description -->
  <xsl:template match="ContentDescription[DescriptionType='Content description']">
    <momaf:hasContentDescription rdf:datatype="rdf:HTML">
      <xsl:attribute name="xml:lang"><xsl:apply-templates select="Language"/></xsl:attribute>
      <xsl:value-of select="DescriptionText"/>
    </momaf:hasContentDescription>
  </xsl:template>

    <!-- Content description language, see thempate above -->
  <xsl:template match="ContentDescription/Language"><xsl:value-of select="text()"/></xsl:template>

  
  <!--xsl:template match="DescriptionType">
    <rdfs:label xml:lang="{../Language/text()}"><xsl:apply-templates/></rdfs:label>
  </xsl:template>
  <xsl:template match="DescriptionText">
    <rdfs:comment  xml:lang="{../Language/text()}"><xsl:apply-templates/></rdfs:comment>
  </xsl:template-->


</xsl:stylesheet>
