import xapian
from ordf.graph import Graph, ConjunctiveGraph
from ordf.vocab.ore import Aggregation
from ordf.namespace import RDF, RDFS, DC, FOAF, ORE
from logging import getLogger

log = getLogger(__name__)

VAL_URI = 0
VAL_LABEL = 1
VAL_TITLE = 2
VAL_NAME = 3

def index_store(store):
    for s,p,o in ConjunctiveGraph(store=store).triples((None, RDF["type"], ORE["Aggregation"])):
        yield index_aggregate(Aggregation(store=store, identifier=s))

def index_aggregate(a):
    doc = xapian.Document()
    doc.add_value(VAL_URI, a.identifier)
    docid = u"URI" + a.identifier
    doc.add_term(docid)

    log.debug("Aggregate: %s" % a.identifier)

    def add_value(g, val_id, subject, predicate):
        val = []
        for s,p,o in g.triples((subject, predicate, None)):
            if not o.language or o.language == "en": ### TODO: fix this
                val.append(o)
        if val:
            val = u", ".join(val)
            doc.add_value(val_id, val)
            return val


    ## create an abbreviated graph to store in the xapian database
    extract = Graph()
    add_value(a, VAL_LABEL, a.identifier, RDFS.label)
    for g in a.contexts():
        log.debug("Indexing: %s" % g.identifier)

        for pred in (RDF.type, RDFS.label, RDFS.comment, DC.title, DC.description, FOAF.name):
            for statement in a.triples((g.identifier, pred, None)):
                extract.add(statement)
        title = add_value(g, VAL_TITLE, g.identifier, DC.title)
        if title:
            doc.add_term(u"ZT" + title[:160])
        name = add_value(g, VAL_NAME, g.identifier, FOAF.name)
        if name:
            doc.add_term(u"NA" + name[:160])
    doc.set_data(extract.serialize(format="n3"))

    ## take any fields that contain text, stem them according to their
    ## language (or english if unsupported or unspecified) and put them
    ## in the index
    termgen = xapian.TermGenerator()
    termgen.set_document(doc)
    for pred in (RDFS.label, RDFS.comment, DC.title, DC.description,
                 FOAF.name, FOAF.first_name, FOAF.last_name, FOAF.surname):
        for s,p,o in a.triples((None, pred, None)):
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
