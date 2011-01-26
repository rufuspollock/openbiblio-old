from ordf.term import Literal, Node, URIRef

def coerce_uri(x):
    if not isinstance(x, URIRef):
        if isinstance(x, Node):
            raise TypeError(x, type(x), "must be URIRef or a type other than Node")
        x = URIRef(x)
    return x

def coerce_literal(x):
    if not isinstance(x, Literal):
        if isinstance(x, Node):
            raise TypeError(x, type(x), "must be Literal or a type other than Node")
        x = Literal(x)
    return x

    
