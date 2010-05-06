import xapian
from ordf.graph import Graph
from ordf.namespace import RDF, RDFS, DC, FOAF

VAL_URI = 0
VAL_TITLE = 1

def index_graph(g):
    doc = xapian.Document()
    doc.add_value(VAL_URI, g.identifier.encode("utf-8"))

    ## create an abbreviated graph to store in the xapian database
    extract = Graph()
    for pred in (RDF.type, RDFS.label, RDFS.comment, DC.title, DC.description, FOAF.name):
        for statement in g.triples((None, pred, None)):
            extract.add(statement)
    doc.set_data(extract.serialize(format="n3"))

    ## store title or other brief descriptive text in a value
    title_done = False
    for pred in (RDFS.label, DC.title, FOAF.name):
        for s,p,o in g.triples((g.identifier, pred, None)):
            doc.add_value(VAL_TITLE, o.encode("utf-8"))
            title_done = True
            break
        if title_done:
            break

    ## take any fields that contain text, stem them according to their
    ## language (or english if unsupported or unspecified) and put them
    ## in the index
    termgen = xapian.TermGenerator()
    termgen.set_document(doc)
    for pred in (RDFS.label, RDFS.comment, DC.title, DC.description,
                 FOAF.name, FOAF.first_name, FOAF.last_name, FOAF.surname):
        for s,p,o in g.triples((None, pred, None)):
            if o.language:
                try:
                    stemmer = xapian.Stem(o.language)
                except xapian.InvalidArgumentError:
                    stemmer = xapian.Stem("en")
            else:
                stemmer = xapian.Stem("en")
            termgen.set_stemmer(stemmer) 
            termgen.index_text(o)
            termgen.increase_termpos()

    return g.identifier, doc
