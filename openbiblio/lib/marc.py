'''
Parse marc data into a suitable form for DB.
'''

from ordf.graph import Graph
from ordf.term import Literal, URIRef, BNode
from ordf.namespace import *

from time import strptime
from swiss import date
from pprint import pprint
import logging
import pymarc
import re

log = logging.getLogger(__name__)

# ===========================================================
# PDW from scratch MARC Parser

def _description():
    """
    MARC fields 500-599 except 506, 530, 540, 546
    """
    exclude = [506, 530, 540, 546]
    for i in range(500,600):
        if i in exclude: continue
        yield (str(i), None, None)

###
### Dublin Core Mapping: http://www.loc.gov/marc/marc2dc.html
### MARC Spec: http://www.loc.gov/marc/bibliographic/ecbdlist.html
###
dcmap = {
    "dc:contributor": (
# 100,700 handled by special case in parser to obtain dates of
# birth and death
#        ("100", "a", None),
        ("110", None, None),
        ("111", None, None),
#        ("700", "a", None), 
        ("710", None, None),
        ("711", "e", None),
        ("720", None, None),
        ),
    "dc:coverage": (
        ("651", None, None),
        ("662", None, None),
        ),
    "dc:date": (
        ("260", "c", None),
        ("260", "g", None),
        ),
    "dc:format": (
        ("340", None, None),
        ("856", "q", None),
        ),
    "bibo:lccn": (
        ("010", "a", None),
        ),
    "marc:lccnc": (
        ("010", "z", None),
        ),
    "marc:lccall_class": (
        ("050", "a", None),
        ),
    "marc:lccall_item": (
        ("050", "b", None),
        ),
    "marc:lccall_mat": (
        ("050", "3", None),
        ),
    "marc:lccopy_class": (
        ("051", "a", None),
        ),
    "marc:lccopy_item": (
        ("051", "b", None),
        ),
    "marc:lccopy_copy": (
        ("051", "c", None),
        ),
    "dc:identifier": (
        ("024", "a", None),
        ),
    "marc:ocn": (
        ("084", "a", None),
        ),
    "marc:ocns": (
        ("084", "2", None),
        ),
    "foaf:page": (
        ("856", "u", None),
        ),
    "marc:nbn": (
        ("015", "a", None),
        ),
    "marc:nbnc": (
        ("015", "2", None),
        ),
    "marc:scn": (
        ("035", "a", None),
        ),
    "marc:scnc": (
        ("035", "z", None),
        ),
    "dc:rightsHolder": (
        ("038", None, None),
        ),
    "dc:spatial": (
        ("043", None, None), ## TODO: normalise geographic representation
        ),
    "dc:language": [("041", x, None) for x in "abdefghj"] + [("546", None, None)],
    "marc:publoc": (
        ("260", "a", None),
        ("044", None, None),
        ),
    "dc:publisher": (
        ("260", "b", None),
        ),
    "dc:relation": [("530", None, None)] + \
                    [(str(x), "o", None) for x in range(760, 788)] + \
                    [(str(x), "t", None) for x in range(760, 788)],
    "dc:rights": (
        ("506", None, None),
        ("540", None, None),
        ),
    "dc:source": (
        ("534", "t", None),
        ("786", "o", None),
        ("786", "t", None),
        ),
    "bibo:isbn": (
        ("020", "a", None),
        ),
    "bibo:issn": (
        ("022", "a", None),
        ),
    "obp:nlmcall": (
        ("060", None, None),
        ),
    "marc:scc": (
        ("072", "a", None),
        ),
    "marc:scc2": (
        ("072", "x", None),
        ),
    "marc:scc3": (
        ("072", "2", None),
        ),
    "marc:ddc": (
        ("082", "a", None),
        ("082", "b", None),
        ),
    "obp:sidcs": (
        ("086", "a", "0"),
        ),
    "obp:gococ": (
        ("086", "a", "1"),
        ),
    "marc:lcsh": (
        ("630", None, None),
        ("650", None, None),
        ),
    "dc:subject": [(str("%03d" % x), None, None) for x in
                    (80, 610, 611, 653, 690)],
    "marc:topic_person_name": (
        ("600", "a", None),
        ),
    "marc:topic_person_title": (
        ("600", "c", None),
        ),
    "marc:topic_person_dates": (
        ("600", "d", None),
        ),
    "marc:topic_person_fullname": (
        ("600", "q", None),
        ),
    "dc:title": [(str(x), None, None) for x in (210, 222, 240, 242, 243, 245, 246, 247)],
    "obp:topic": (
        ("655", None, None),
        ),
    "dc:isPartOf": (
        ("800", None, None),
        ("810", None, None),
        ("811", None, None),
        ("830", None, None),
        ),
    "dc:alternative": [(str(x), None, None) for x in (130, 210, 240, 242, 246, 730, 740)],
    "dc:accrualPeriodicity": (
        ("310", "a", None),
        ),
    "obp:pubnum": (
        ("028", "a", None),
        ),
    "marc:charset": (
        ("066", None, None),
        ),
    "obp:edition": (
        ("250", None, None),
        ),
    "dc:extent": (
        ("300", "a", None), # extent
        ),
    "obp:physicalDetail": (
        ("300", "b", None), # physical detail characteristics
        ),
    "obp:dimensions": (
        ("300", "c", None), # dimensions
        ),
    "obp:accompanyingMaterial": (
        ("300", "e", None), # accompanying material
        ),
    "obp:typeOfUnit": (
        ("300", "f", None), # type of unit
        ),
    "obp:sizeOfUnit": (
        ("300", "g", None),
        ),
    "dc:description": list(_description()),
    "obp:pubseq": (
        ("362", None, None),
        ),
    "marc:spatialResolution": (
        ("255", None, None),
        ),
    
}

### XXX TODO: handle 007 (physical description and 008 general information)
_handled_fields = reduce(lambda x,y: x+y,
                 [[spec[0] for spec in x] for x in dcmap.values()] + \
                 [["001", "003", "005", "007", "008", "029", "035", "040", "042"],
                  ["019"],  # unknown, not in MARC spec
                  ["049",], # found in test data with value CUDA, not in MARC spec
                  ["069"],  # found in Yale MARC file, not in spec
                  ["100", "700"], # authors handled as special case
                  ["440", "490"],
                  ["%03d" % x for x in range(690, 700)], # local significance
                  ["880"],  # alternat graphical representation
                  ["%03d" % x for x in range(90,100)], # local fields
                  map(str, range(900,1000)),                # local fields
                 ])

class _Clean(object):
    """
    Cleaner for MARC data. Call an instance of this class with an
    (RDF) field name and it will return a function that cleans the
    data.
    """
    def __call__(self, field):
        from openbiblio.lib.name import normalize as name
        if field in ("dc:contributor", "marc:topic_person_name", "marc:topic_person_fullname"):
            return lambda x: Literal(name(x))
        elif field in ("dc:date",):
            return self.date
        elif field in ("dc:subject",):
            return self.subject
        elif field in ("bibo:isbn", "bibo:issn"):
            return self.isbn
        elif field in ("foaf:page", "foaf:homepage"):
            return self.uri
        return self.default

    def default(self, s):
        s = s.rstrip(" :"). \
            rstrip(" /"). \
            rstrip(","). \
            rstrip("."). \
            strip()
        try:
            s = s.decode("utf-8")
        except UnicodeError:
            s = s
        return Literal(s)

    def uri(self, s):
        return URIRef(s)

    def isbn(self, s):
        return Literal(s.replace(" ", "").replace("-", ""))

    def subject(self, subject):
        return Literal(subject)

    def dates(self, dates_str):
        if not dates_str:
            return (None, None)
        out = dates_str.rsplit("-", 1)
        if len(out) == 1:
            return self.date(out[0]), None
        return map(self.date, out)

    def date(self, d):
        parsed = date.parse(d)
        if parsed is None:
            return None
        iso = parsed.isoformat()
        if iso:
            val = iso
        else:
            val = parsed.qualifier
        if len(val) == 4:
            return Literal(val, datatype=XSD.year)
        try:
            strptime(val, "%Y-%m-%d")
            return Literal(val, datatype=XSD.date)
        except ValueError:
            return Literal(val)

_clean = _Clean()
def _force_unicode(s):
    if isinstance(s, unicode):
        return s
    try:
        return s.decode("utf-8")
    except UnicodeError:
        return s.decode("latin1")

    # special case for authors
class Record(object):
    def __init__(self, marc):
        self._marc = marc
        def _field_dict(f):
            _d = {
                "value": f.value(),
                "subfields": {},
                }
            if hasattr(f, "indicators"):
                _d["indicators"] = f.indicators
            else:
                _d["indicators"] = []
            if hasattr(f, "subfields"):
                for i in range(len(f.subfields)/2):
                    subf = f.subfields[i*2]
                    subv = f.subfields[i*2+1]
                    _d["subfields"].setdefault(subf, []).append(subv)
            return _d
        self._dict = {}
        for field in marc.fields:
            values = self._dict.setdefault(field.tag, [])
            values.append(_field_dict(field))

    def __str__(self):
        return str(self._marc)
    def __repr__(self):
        return str(self._marc)
    
    def get_field(self, field, subfield=None, indicator=None):
        """
        Return a flattened list of all entries for a given field/subfield
        """
        def _indicated(f):
            if indicator is None:
                return True
            if isinstance(indicator, basestring):
                if f["indicators"][0] == indicator:
                    return True
            else:
                if f["indicators"] == indicator:
                    return True
            return False

        def _subfields(f):
            if subfield is not None:
                subfields = [f["subfields"].get(subfield, [])]
            else:
                subfields = f["subfields"].values()
            return reduce(lambda x,y: x+y, subfields)

        value = self._dict.get(field, [])        
        result = [_subfields(f) for f in value if _indicated(f)]
        if result:
            result = reduce(lambda x,y: x+y, result)
        return [_force_unicode(x) for x in result if x]

            
    # special case for authors
    def get_authors(self):
        authors = self.get_field("100", "a") + self.get_field("700", "a")
        dates = self.get_field("100", "d") + self.get_field("700", "d")
        if len(authors) != len(dates) and len(dates) > 0:
            log.warning("unparsable authors: %s dates %s" % (authors, dates))
            return []
        authors = map(_clean("dc:contributor"), authors)
        if len(dates) == 0:
            return [ { "foaf:name": [x] } for x in authors]
        dates = map(_clean.dates, dates)
        def _a2d(a):
            name, (birth, death) = a
            d = { "rdf:type": [FOAF["Person"]], "foaf:name": [name] }
            if birth or death:
                d["bio:event"] = []
            if birth:
                d["bio:event"].append({
                    "rdf:type": [BIO["Birth"]],
                    "bio:date": [birth]
                    })
            if death:
                d["bio:event"].append({
                    "rdf:type": [BIO["Death"]],
                    "bio:date": [death]
                    })
            return d
        return [ _a2d(x) for x in zip(authors, dates)]

    def contributors(self, result):
        authors = self.get_authors()
        return authors + [ { "foaf:name": [x] } for x in result ]

    def subject_person(self):
        name = self["marc:topic_person_name"]
        fullname = self["marc:topic_person_fullname"]
        dates = map(_clean.dates, self["marc:topic_person_dates"])
        title = self["marc:topic_person_title"]
        if not name and not fullname:
            return []
        info = {
            "rdf:type": [FOAF["Person"]],
            "foaf:name": name + fullname,
            "foaf:title": title,
            "bio:event": [],
            }
        for birth, death in dates:
            if birth:
                info["bio:event"].append({
                        "rdf:type": [BIO["Birth"]],
                        "bio:date": [birth]
                        })
            if death:
                info["bio:event"].append({
                        "rdf:type": [BIO["Death"]],
                        "bio:date": [death]
                        })
        return [info]

    def title(self, result):
        title = []
        for part in result:
            if part.startswith("[by] ") or part.startswith("by "):
                continue
            title.append(part)
        return [Literal("\n".join(title))]

    def __getitem__(self, key):
        spec = dcmap[key]
        result = [self.get_field(*s) for s in spec]
        if result:
            result = reduce(lambda x,y: x+y, result)
        cleaner = _clean(key)
        result = map(cleaner, result)
        if key in ("dc:contributor",):
            return self.contributors(result)
        elif key in ("dc:title",): # special case to preserve title
            return self.title(result)
        elif key in ("dc:subject",):
            return result + self.lcsh() + self.ddc() + self.scc() + self.ocn() + self.subject_person() + self.index_term()
        elif key in ("dc:publisher",):
            return self.publisher(result)
        elif key in ("dc:isPartOf",):
            return self.isPartOf()
        return result

    def frag(self):
        class Frag(Graph):
            def __init__(frag, field):
                Graph.__init__(frag)
                frag.field = field
                frag()

            def add_field(frag, predicate, subfield, termtype=Literal):
                for x in self.get_field(frag.field, subfield):
                    frag.add((frag.identifier, predicate, termtype(x)))
        return Frag

    def isPartOf(self, g):
        class Part(self.frag()):
            def __call__(self):
                self.add_field(RDFS["label"], "a")
                self.add_field(DC["spatial"], "c")
                self.add_field(DC["date"], "d")
                self.add_field(DC["description"], "g")
                self.add_field(DC["lang"], "l")
                self.add_field(OBP["part"], "p")
                self.add_field(DC["version"], "s")
                self.add_field(OBP["volume"], "v")
                self.add_field(DC["title"], "t"),
                self.add_field(DC["identifier"], "w")
                self.add_field(BIBO["issn"], "x")
                return self

        person = Part("800")
        if person:
            g.add((g.identifier, OBP["personalName"], person.identifier))
            g.add((g.identifier, DC["isPartOf"], person.identifier))
            g += person

        corp = Part("810")
        if corp:
            g.add((g.identifier, OBP["corporateName"], corp.identifier))
            g.add((g.identifier, DC["isPartOf"], corp.identifier))
            g += corp

        meeting = Part("811")
        if meeting:
            g.add((g.identifier, OBP["meetingName"], meeting.identifier))
            g.add((g.identifier, DC["isPartOf"], meeting.identifier))
            g += meeting

        uniform = Part("830")
        if uniform:
            g.add((g.identifier, OBP["uniformTitle"], uniform.identifier))
            g.add((g.identifier, DC["isPartOf"], uniform.identifier))
            if not uniform.exists((uniform.identifier, DC["title"], None)):
                uniform += uniform.replace(
                        (uniform.identifier, RDFS["label"], None), (None, DC["title"], None)
                        )

            g += uniform

    def subfields(self, field):
        _subfields = field.subfields
        subfields = {}
        for i in range(len(_subfields)/2):
            subfields[_subfields[i*2]] = _force_unicode(_subfields[i*2+1])
        return field, subfields

    def index_term(self):
        terms = []
        for f,s in map(self.subfields, self._marc.get_fields("655")):
            d = {}
            d["obp:thesaurus"] = [Literal(f.indicator2)]
            if "a" in s: d["rdf:value"] = [Literal(s["a"])]
            if "x" in s: d["foaf:topic"] = [Literal(s["x"])]
            if "y" in s: d["dc:date"] = [Literal(s["y"])]
            if "z" in s: d["dc:spatial"] = [Literal(s["z"])]
            terms.append(d)
        return terms


    def lcsh(self):
        subjects = []
        for sh in self["marc:lcsh"]:
            subjects.append({
                    "dcam:member": [DC["LCSH"]],
                    "rdf:value": [sh]
                    })
        return subjects

    def ddc(self):
        ddc = []
        for s in self["marc:ddc"]:
            try:
                c, rest = s.split(".", 1)
            except:
                c = s
            ddc.append({
                    "dcam:member": [DC["DDC"]],
                    "rdf:value": [s],
                    "rdfs:seeAlso": [URIRef("http://dewey.info/class/%s/" % c)]
                    })
        return ddc

    def scc(self):
        scc = self["marc:scc"]
        scc2 = self["marc:scc2"]
        thesaurus = self["marc:scc3"]
        if scc2: 
            print scc, scc2, thesaurus
            raise
        if scc:
            if thesaurus == ["lcco"]:
                return [{
                        "dcam:member": [DC["LCC"]],
                        "rdf:value": scc,
                        }]
            else:
                raise ValueError("Unknown SCC Thesaurus: %s" % thesaurus)
        return []

    def ocn(self):
        """
        Other Classification Number
        http://www.loc.gov/standards/sourcelist/classification.html
        """
        ocn = self["marc:ocn"]
        ocns = self["marc:ocns"]
        subj = []
        for n, s in zip(ocn, ocns):
            subj += [{
                    "dcam:member": [SCCS[s]],
                    "rdf:value": [n]
                    }]
        return subj

    def publisher(self, publisher):
        if publisher:
            result = [{
                    "rdf:type": [DC["Agent"]],
                    "foaf:name": publisher,
                    "dc:spatial": self["marc:publoc"],
                    }]
        else:
            result = []
        return result

    def nbn(self, g):
        """
        Add urn:nbn: identifiers for national bibliographic
        numbers per:

        http://www.ietf.org/rfc/rfc3188.txt

        TODO: transform nbn prefixes to ISO country codes
        """
        nbn = self["marc:nbn"]
        nbnc = self["marc:nbnc"]
        if nbn and nbnc:
            for n, c in zip(nbn, nbnc):
                g.add((g.identifier, RDFS["seeAlso"], URIRef("urn:nbn:%s-%s" % (c, n))))
                b = BNode()
                g.add((g.identifier, OBP["nbn"], b))
                g.add((b, DCAM["member"], NBN[c]))
                g.add((b, RDF["value"], n))

    def scn(self, g):
        """
        Process system control numbers
        """
        _scnre = re.compile(r'\((?P<org>[a-zA-Z]+)\)(?P<num>.*)')
        scn = self["marc:scn"]
        for m in map(_scnre.match, scn):
            if not m:
                log.warning("Invalid SCN: %s" % scn)
                continue
            d = m.groupdict()
            b = BNode()
            g.add((g.identifier, OBP["scn"], b))
            g.add((b, DCAM["member"], SCN[d["org"]]))
            g.add((b, RDF["value"], Literal(d["num"])))
        scnc = self["marc:scnc"]
        for m in map(_scnre.match, scnc):
            if not m:
                log.warning("Invalid cancelled SCN: %s" % scnc)
                continue
            d = m.groupdict()
            b = BNode()
            g.add((g.identifier, OBP["scn"], b))
            g.add((b, DCAM["member"], SCN[d["org"]]))
            g.add((b, OBP["cancelled"], Literal(d["num"])))
        for n in self["bibo:lccn"]:
            b = BNode()
            g.add((g.identifier, OBP["scn"], b))
            g.add((b, DCAM["member"], SCN["DLC"]))
            g.add((b, RDF["value"], n))
        for n in self["marc:lccnc"]:
            b = BNode()
            b = BNode()
            g.add((g.identifier, OBP["scn"], b))
            g.add((b, DCAM["member"], SCN["DLC"]))
            g.add((b, RDF["cancelled"], n))

    def lccall(self, g):
        cls = self["marc:lccall_class"]
        item = self["marc:lccall_item"]
        for c,i in zip(cls, item):
            b = BNode()
            g.add((g.identifier, OBP["lccall"], Literal(c+i)))

    def lccopy(self, g):
        cls = self["marc:lccopy_class"]
        item = self["marc:lccopy_item"]
        copy = self["marc:lccopy_copy"]
        if cls + item + copy:
            b = BNode()
            g.add((g.identifier, OBP["lccopy"], b))
            for c,i in zip(cls, item):
                g.add((b, OBP["lccall"], Literal(c + i)))
            for c in copy:
                g.add((b, DC["description"], c))
                
    def keys(self):
        return dcmap.keys()

    def charset(self):
        ## TODO
        pass

    def items(self):
        for k in self.keys():
            if k in ("marc:lcsh", "marc:ddc",
                     "marc:scc", "marc:scc2", "marc:scc3",
                     "marc:publoc", "marc:charset",
                     "marc:nbn", "marc:nbnc",
                     "marc:scn", "marc:scnc",
                     "marc:lcnc",
                     "marc:ocn", "marc:ocns",
                     "marc:lccopy_class", "marc:lccopy_item", "marc:lccopy_copy",
                     "marc:lccall_class", "marc:lccall_item", "marc:lccall_mat",
                     "marc:topic_person_name", "marc:topic_person_fullname", 
                     "marc:topic_person_dates", "marc:topic_person_title",
                     "dc:isPartOf",
                     ):
                continue
            v = self[k]
            if v: yield k,v
            
    def sanity(self):
        for field in self._marc.fields:
            if field.tag not in _handled_fields:
                pprint (self._dict)
                raise KeyError(field.tag)

    def rdf(self, *av, **kw):
        g = Graph(*av, **kw)
        g.add((g.identifier, RDF["type"], OBP["MarcRecord"]))
        def merge(d, s):
            for k,v  in d.items():
                ns, term = k.split(":")
                p = namespaces[ns][term]
                for o in v:
                    if isinstance(o, dict):
                        b = BNode()
                        g.add((s, p, b))
                        merge(o, b)
                    else:
                        g.add((s, p, o))

        ident = g.identifier
        merge(self, ident)

        for s,p,o in g.triples((ident, BIBO["isbn"], None)):
            g.add((ident, RDFS["seeAlso"], URIRef("urn:isbn:%s" % o)))
            g.add((ident, RDFS["seeAlso"], URIRef("http://purl.org/NET/book/isbn/%s#book" % o)))
            g.add((ident, RDFS["seeAlso"], URIRef("http://www4.wiwiss.fu-berlin.de/bookmashup/books/%s" % o)))
            if len(o) == 10:
                g.add((ident, BIBO["isbn10"], o))
            elif len(o) == 13:
                g.add((ident, BIBO["isbn13"], o))

        for s,p,o in g.triples((ident, BIBO["issn"], None)):
            g.add((ident, RDFS["seeAlso"], URIRef("urn:issn:%s" % o)))

        for s,p,o in g.triples((ident, BIBO["lccn"], None)):
            g.add((ident, RDFS["seeAlso"], URIRef(u"http://lccn.loc.gov/" + o)))

        self.nbn(g)
        self.scn(g)
        self.lccall(g)
        self.lccopy(g)
        self.isPartOf(g)

        return g

class Parser(object):
    def __init__(self, f):
        if isinstance(f, basestring):
            f = file(f)
        self._reader = pymarc.reader.MARCReader(f)
        
    def __iter__(self):
        for marc in self._reader:
            yield Record(marc)

