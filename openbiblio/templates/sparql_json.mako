<%
    from pprint import pformat
    from ordf.term import URIRef, Literal
    try:
        from rdflib.term import BNode
    except ImportError:
        from rdflib import BNode
    try:
        import json
    except ImportError:
        import simplejson as json

    def json_result(c):
        d = {}
        d["head"] = { "link": c.url }
        if c.bindings:
            d["head"]["vars"] = ["%s" % b for b in c.bindings]
            d["results"] = {
                "bindings": [json_row(c.bindings, r) for r in c.results]
            }
        else:
            d["boolean"] = c.boolean
        if c.warnings:
            d["warnings"] = c.warnings
        return json.dumps(d)

    def json_row(bindings, row):
        d = {}
        for b in bindings:
            val = {}
            col = row[b]
            val["value"] = str(col)
            if isinstance(col, BNode):
                val["type"] = col
            elif isinstance(col, URIRef):
                val["type"] = "uri"
            elif isinstance(col, Literal):
                val["type"] = "literal"
                if col.datatype:
                    val["datatype"] = col.datatype
                if col.language:
                    val["lang"] = col.language
            d["%s" % b] = val
        return d
%>${ json_result(c) | n}
