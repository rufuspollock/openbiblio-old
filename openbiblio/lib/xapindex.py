import xapian
from ordf.graph import Graph
from ordf.namespace import RDF, RDFS, DC, FOAF

VAL_URI = 0
VAL_LABEL = 1
VAL_TITLE = 2
VAL_NAME = 3

def index_graph(g):
    doc = xapian.Document()
    doc.add_value(VAL_URI, g.identifier)
    docid = u"URI" + g.identifier
    doc.add_term(docid)

    ## create an abbreviated graph to store in the xapian database
    extract = Graph()
    for pred in (RDF.type, RDFS.label, RDFS.comment, DC.title, DC.description, FOAF.name):
        for statement in g.triples((g.identifier, pred, None)):
            extract.add(statement)
    doc.set_data(extract.serialize(format="n3"))

    def add_value(val_id, predicate):
        val = []
        for s,p,o in g.triples((g.identifier, predicate, None)):
            if not o.language or o.language == "en": ### TODO: fix this
                val.append(o)
        if val:
            val = u", ".join(val)
            doc.add_value(val_id, val)
            return val
    add_value(VAL_LABEL, RDFS.label)
    title = add_value(VAL_TITLE, DC.title)
    if title:
        doc.add_term(u"ZT" + title[:160])
    name = add_value(VAL_NAME, FOAF.name)
    if name:
        doc.add_term(u"NA" + name[:160])

    ## take any fields that contain text, stem them according to their
    ## language (or english if unsupported or unspecified) and put them
    ## in the index
    termgen = xapian.TermGenerator()
    termgen.set_document(doc)
    for pred in (RDFS.label, RDFS.comment, DC.title, DC.description,
                 FOAF.name, FOAF.first_name, FOAF.last_name, FOAF.surname):
        for s,p,o in g.triples((None, pred, None)):
            termgen.increase_termpos()
            if o.language:
                try:
                    stemmer = xapian.Stem(o.language)
                except xapian.InvalidArgumentError:
                    stemmer = xapian.Stem("en")
            else:
                stemmer = xapian.Stem("en")
            termgen.set_stemmer(stemmer) 
            termgen.index_text(o)

    return docid, doc

def search(xap, query_string, offset, limit):
    qp = xapian.QueryParser()
    qp.add_prefix("name", "NA")
    qp.add_prefix("title", "ZT")

    stemmer = xapian.Stem("en") ## TODO other languages
    qp.set_stemmer(stemmer)
    qp.set_stemming_strategy(xapian.QueryParser.STEM_SOME)
    qp.set_database(xap)

    search_flags = (
        xapian.QueryParser.FLAG_BOOLEAN |
        xapian.QueryParser.FLAG_AUTO_MULTIWORD_SYNONYMS |
        xapian.QueryParser.FLAG_LOVEHATE
    )
    query = qp.parse_query(query_string, search_flags)

    enquire = xapian.Enquire(xap)
    enquire.set_query(query)
    return enquire.get_mset(offset, limit)
