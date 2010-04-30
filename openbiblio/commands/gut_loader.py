from openbiblio.commands.marc_loader import Loader as MARCLoader
from ordf.term import Literal, URIRef
from pprint import pprint
import re
import sys

_re_num = re.compile(r"^[0-9]+$")

class Loader(MARCLoader):
    summary = "Load Project Gutenberg MARC dump"
    def collection_name(self):
        name = self.options.collection
        if name is None: name = "gutenberg"
        return name

    def load(self, record):
        self.clean_identifiers(record)
        self.clean_subjects(record)
        self.clean_partof(record)
        super(Loader, self).load(record)

    def clean_identifiers(self, record):
        identifiers = record.get("dc:identifier", [])
        links = []
        rights = []
        idents = []
        for i in range(len(identifiers)):
            ident = identifiers[0]
            if ident.startswith("http://") and not ident.endswith("license"):
                links.append( URIRef(ident) )
            elif ident.endswith("license"):
                rights.append( URIRef(ident) )
            else:
                idents.append(ident)
            identifiers = identifiers[1:]
        record["dc:identifier"] = idents
        record["dc:rights"] = rights
        record["foaf:homepage"] = links

    def clean_subjects(self, record):
        subjects = []
        for s in record.get("dc:subject", []):
            if s == u"[electronic resource]":
                continue
            subjects.append(s)
        record["dc:subject"] = subjects

    def clean_partof(self, record):
        parts = []
        for part in record.get("dc:isPartOf", []):
            if part == "Porject Gutenberg":
                parts.append(Literal("Project Gutenberg"))
            elif _re_num.match(part):
                ident = record.get("dc:identifier", [])
                ident.append(Literal("PG%s" % (part,)))
                record["dc:identifier"] = ident
            else:
                parts.append(part)
        record["dc:isPartOf"] = parts

    def record_subject(self, record):
        page = record.get("foaf:homepage", None)
        if page is None:
            return super(Loader, self).record_subject(record)
        del record["foaf:homepage"]
        return page[0]
