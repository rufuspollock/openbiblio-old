# -*- coding=utf-8 -*-
#!/usr/bin/env python

# NOTE - may have to invoke a Unicode to Latex converter at some point
# as there are still many who don't have a unicode-enabled version.
# --- http://code.activestate.com/recipes/252124-latex-codec/ for eg

 
from ordf.graph import Graph
from ordf.term import URIRef
from ordf.namespace import Namespace, DC, RDFS, SKOS, RDF, BIBO

ISBD = Namespace("http://iflastandards.info/ns/isbd/elements/")

# simple mappings:  (eg <uri> <pred> "...")
SIMPLE_MAPPING = {DC['title']:"title",
                 ISBD['hasEditionStatement']:"edition",
                 DC["issued"]:"year",
                 }

# Blank node mappings (eg <uri> <pred> [ <pred> "..." ])
BNODE_MAPPING = {DC["contributor"]:(SKOS["notation"], "author"),
                DC["editor"]:(SKOS["notation"], "editor"),
                DC["extent"]:(RDFS['label'], "extent"),
                ISBD["hasPlaceOfPublicationProductionDistribution"]:(RDFS['label'], "address"),
                DC['language']:(RDF['value'], "language"),
                }

TYPE_MAPPING = {BIBO['Book']:"Book",
                BIBO['Article']:"Article",
                }

class Bibtex(object):
    """Simple container to manage the conversion into Bibtex"""
    def __init__(self):
        # set some defaults
        self.btype = None # bibtex requires a type. 'misc' might be a good alt default
        self.uniquekey = "" # bibtex requires a unique key for the 'record'
        #                     aim is to use the GB0.. for the BL books as URI may break bibtex
        self.uri = None       # This will hold the URI for the document it holds the citation for
        self.bibtex = {}  # key values

    def load_from_graph(self, graph):
        # 1 - find type
        # 2 - load key, values
        # 3 - get unique id

        # 1 - get the bibo:Document URI and then find the other URI types:
        matched_uris = list(s for s,p,o in graph.triples((None, RDF['type'], BIBO['Document'])))
        if not matched_uris:
            print "Failed to find a bibo:Document within the submitted graph. Load failed."
            return False
        # Using the first one
        self.uri = matched_uris.pop(0)
        # get all types
        types = list(o for s,p,o in graph.triples((self.uri, RDF['type'], None)))
        while(not self.btype and types):
            type_uri = types.pop()
            self.btype = TYPE_MAPPING.get(type_uri, None)
        
        if not self.btype:
            self.btype = "misc"  # or should we assume 'Book'

        # 2 get key + values
        # mappings:
        for s,p,o in graph.triples((self.uri, None, None)):
            if p in SIMPLE_MAPPING.keys():
                if SIMPLE_MAPPING[p] not in self.bibtex.keys():
                    self.bibtex[SIMPLE_MAPPING[p]] = []
                self.bibtex[SIMPLE_MAPPING[p]].append(o)
            elif p in BNODE_MAPPING.keys():
                if BNODE_MAPPING[p][1] not in self.bibtex.keys():
                    self.bibtex[BNODE_MAPPING[p][1]] = []
                for bn, bpred, bo in graph.triples((o, BNODE_MAPPING[p][0], None)):
                    self.bibtex[BNODE_MAPPING[p][1]].append(bo)
                
        # 3 - Unique id for bibtex
        gb_id = list(o for _,_,o in graph.triples((self.uri, BIBO["identifier"], None)))
        # assert id == 1?
        if len(gb_id) == 1:
            self.uniquekey = gb_id.pop()
        else:
            # Umm... author concatenate?... hash of uri?
            pass

    def __repr__(self):
        if self.uri:
            return "URI: %s\nType: %s\nUnique Bibtex ID: %s\n - %s\n" % (self.uri, self.btype, self.uniquekey, " - ".join("%s: %s\n" % (k,v) for k,v in self.bibtex.items()))
        else:
            return "No data loaded"

    def to_bibtex(self):
        if not self.uri:
            return
        else:
            bibtext = "@%s { %s,\n" % (self.btype, self.uniquekey)
            for k in sorted(self.bibtex.keys()):
                bibtext += " " * (len(self.btype) + 4)
                # TODO! Escape unicode and bad chars
                bibtext += '%s = "%s" ,\n' % (k, " ; ".join(self.bibtex[k]).replace('"', "'"))
            bibtext += "}\n"
            return bibtext
            

"""
BIBTEX information
==================

Info from http://en.wikipedia.org/wiki/BibTeX as bibtex.org was down :)

@TYPE{UNIQUEKEY,
KEY = VALUE,
KEY2 = VALUE2,
....
etc
....
}

eg

@Book{abramowitz+stegun,
 author    = "Milton {Abramowitz} and Irene A. {Stegun}",
 title     = "Handbook of Mathematical Functions with
              Formulas, Graphs, and Mathematical Tables",
 publisher = "Dover",
 year      =  1964,
 address   = "New York",
 edition   = "ninth Dover printing, tenth GPO printing"
}

Keys
----

address:
    Publisher's address (usually just the city, but can be the full address for lesser-known publishers)
annote:
    An annotation for annotated bibliography styles (not typical)
author: 
    The name(s) of the author(s) (in the case of more than one author, separated by and)
booktitle: 
    The title of the book, if only part of it is being cited
chapter: 
    The chapter number
crossref: 
    The key of the cross-referenced entry
edition: 
    The edition of a book, long form (such as "first" or "second")
editor: 
    The name(s) of the editor(s)
eprint:
    A specification of an electronic publication, often a preprint or a technical report
howpublished: 
    How it was published, if the publishing method is nonstandard
institution: 
    The institution that was involved in the publishing, but not necessarily the publisher
journal: 
    The journal or magazine the work was published in
key: 
    A hidden field used for specifying or overriding the alphabetical order of entries (when the "author" and "editor" fields are missing). Note that this is very different from the key (mentioned just after this list) that is used to cite or cross-reference the entry.
month: 
    The month of publication (or, if unpublished, the month of creation)
note:
    Miscellaneous extra information
number: 
    The "(issue) number" of a journal, magazine, or tech-report, if applicable. (Most publications have a "volume", but no "number" field.)
organization: 
    The conference sponsor
pages: 
    Page numbers, separated either by commas or double-hyphens.
publisher: 
    The publisher's name
school: 
    The school where the thesis was written
series: 
    The series of books the book was published in (e.g. "The Hardy Boys" or "Lecture Notes in Computer Science")
title: 
    The title of the work
type: 
    The type of tech-report, for example, "Research Note"
url: 
    The WWW address
volume: 
    The volume of a journal or multi-volume book
year: 
    The year of publication (or, if unpublished, the year of creation)

Types
-----

article
    An article from a journal or magazine.
    Required fields: author, title, journal, year
    Optional fields: volume, number, pages, month, note, key

book
    A book with an explicit publisher.
    Required fields: author/editor, title, publisher, year
    Optional fields: volume, series, address, edition, month, note, key

booklet
    A work that is printed and bound, but without a named publisher or sponsoring institution.
    Required fields: title
    Optional fields: author, howpublished, address, month, year, note, key

conference
    The same as inproceedings, included for Scribe compatibility.
    Required fields: author, title, booktitle, year
    Optional fields: editor, pages, organization, publisher, address, month, note, key

inbook
    A part of a book, usually untitled. May be a chapter (or section or whatever) and/or a range of pages.
    Required fields: author/editor, title, chapter/pages, publisher, year
    Optional fields: volume, series, address, edition, month, note, key

incollection
    A part of a book having its own title.
    Required fields: author, title, booktitle, year
    Optional fields: editor, pages, organization, publisher, address, month, note, key

inproceedings
    An article in a conference proceedings.
    Required fields: author, title, booktitle, year
    Optional fields: editor, series, pages, organization, publisher, address, month, note, key

manual
    Technical documentation.
    Required fields: title
    Optional fields: author, organization, address, edition, month, year, note, key

mastersthesis
    A Master's thesis.
    Required fields: author, title, school, year
    Optional fields: address, month, note, key
misc
    For use when nothing else fits.
    Required fields: none
    Optional fields: author, title, howpublished, month, year, note, key

phdthesis
    A Ph.D. thesis.
    Required fields: author, title, school, year
    Optional fields: address, month, note, key

proceedings
    The proceedings of a conference.
    Required fields: title, year
    Optional fields: editor, publisher, organization, address, month, note, key

techreport
    A report published by a school or other institution, usually numbered within a series.
    Required fields: author, title, institution, year
    Optional fields: type, number, address, month, note, key

unpublished
    A document having an author and title, but not formally published.
    Required fields: author, title, note
    Optional fields: month, year, key
"""
