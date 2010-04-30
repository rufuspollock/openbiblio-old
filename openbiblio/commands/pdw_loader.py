from __future__ import with_statement
from openbiblio.commands import Command
from datetime import datetime
from pylons import config
from ordf.term import Literal, URIRef
from ordf.namespace import XSD
from pprint import pprint
import tarfile
import logging
import swiss.date
import swiss.cache
import json
import sys
import os

def _exists(filename):
    try:
        os.stat(filename)
        return True
    except OSError:
        return False

def _date(d):
    if len(d) == 4:
        d = Literal(d, datatype=XSD.year)
    else:
        date = swiss.date.parse(d)
        if date is None:
            d = Literal(d, datatype=XSD.date)
        else:
            d = Literal(date.isoformat(), datatype=XSD.date)
    return d

class Loader(Command):
    summary = "Load Dataset(s)"
    usage = "config.ini dataset [dataset2 [dataset3 [...]]]"
    parser = Command.standard_parser(verbose=False)
    parser.add_option("-e", "--entities",
        dest="load_entities",
        default=False,
        action="store_true",
        help="Load Entities (Person, Work) - exclusive with --links"
    )
    parser.add_option("-l", "--links",
        dest="load_links",
        default=False,
        action="store_true",
        help="Load Links - exclusive with --entities"
    )
    parser.add_option("-d", "--drop",
        dest="drop",
        default=False,
        action="store_true",
        help="Drop data before loading"
    )
    parser.add_option("-f", "--files",
        dest="files",
        default=False,
        action="store_true",
        help="Load given files rather than datasets from the config"
    )
    def command(self):
        self.cache = swiss.Cache(self.config.get("cache_dir", "data"))
        self.log = logging.getLogger("load")
        self.connect()

        if self.options.load_entities and self.options.load_links:
            self.log.error("must specify only one of --entities, --links")
            sys.exit(1)
        if self.options.drop:
            self.log.info("dropping collections")
            self.db.drop_collection("person")
            self.db.drop_collection("person.history")
            self.db.drop_collection("work")
            self.db.drop_collection("work.history")
            self.db.drop_collection("expression")
            self.db.drop_collection("expression.history")
            self.db.drop_collection("work_types")
            self.db.drop_collection("item_types")
        for arg in self.args:
            self.load_json(arg)

    def connect(self):
        from openbiblio.model import mongodb
        self.db = mongodb

    def load_json(self, dataset):
        if self.options.files:
            files = [dataset]
        else:
            url = self.config.get("%s" % (dataset,), None)
            if url is None:
                self.log.error("no download url for dataset %s in config file" % (dataset,))
                return
            archive = self.cache.filepath(url)
            try: os.stat(archive)
            except:
                self.log.error("file %s does not exist. please fetch it first" % (archive,))
            tar = tarfile.open(archive, "r:gz")
            tar.extractall(self.cache.path)
            files = tar.getnames()

        nfiles = 0
        nrecords = 0
        start = datetime.now()

        for fname in files:
            self.log.info("loading %s" % (fname,))
            nfiles += 1

            fpath = os.path.join(self.cache.path, fname)
            if os.path.isdir(fpath):
                continue
            fp = open(fpath, "r+")
            data = json.loads(fp.read())
            fp.close()
            for k in data:
                if self.options.load_entities and k == "Person":
                    self.load_people(data[k])
                if self.options.load_entities and k == "Work":
                    self.load_works(data[k])
                if self.options.load_entities and k == "Item":
                    self.load_expressions(data[k])
                elif self.options.load_links and k == "WorkItem":
                    self.load_item_links(data[k])
                elif self.options.load_links and k == "WorkPerson":
                    self.load_person_links(data[k])

        end = datetime.now()
        self.log.info("Elapsed time: %s" % (end-start,))
        self.log.info("Processed %d files" % (nfiles,))

    def load_people(self, data):
        for record in data:
            _id = "urn:uuid:%s" % record["id"]
            p = self.db.person.Person.get_from_id(_id)
            if p is None:
                p = self.db.person.Person()
                p["_id"] = _id
            if record["name"]:
                p["foaf:name"] = [record["name"]]
            if record["birth_date_normed"]:
                d = record["birth_date_normed"]
                p["dbpprop:dateOfBirth"] = [_date(d)]
            if record["death_date_normed"]:
                d = record["death_date_normed"]
                p["dbpprop:dateOfDeath"] = [_date(d)]
            if record["srcid"]:
                p["dct:source"] = [record["srcid"]]
            if record["notes"]:
                p["dct:description"] = [record["notes"]]
            p.save()

    def load_works(self, data):
        for record in data:
            _id = "urn:uuid:%s" % record["id"]
            w = self.db.work.Work.get_from_id(_id)
            if w is None:
                w = self.db.work.Work()
                w["_id"] = _id
            if record["title"]:
                w["dct:title"] = [record["title"]]
            if record["notes"]:
                w["dct:description"] = [record["notes"]]
            if record["date"]:
                d = record["date_normed"]
                w["dct:date"] = [_date(d)]
            w.save()
            ## for later steps, type really goes in expression
            self.db.work_types.insert({"_id": w["_id"], "type": record["type"]})

    def load_expressions(self, data):
        for record in data:
            _id = "urn:uuid:%s" % record["id"]
            e = self.db.expression.Expression.get_from_id(_id)
            if e is None:
                e = self.db.expression.Expression()
                e["_id"] = _id
            if record["title"]:
                e["dct:title"] = [record["title"]]
            if record["srcid"]:
                e["dct:source"] = [record["srcid"]]
            if record["date_normed"]:
                d = record["date_normed"]
                e["dct:date"] = [_date(d)]
            if record["notes"]:
                e["dct:description"] = [record["notes"]]
            e.save()
            ## for later processing of type
            self.db.item_types.insert({"_id": e["_id"], "type": record["type"]})

    def load_item_links(self, data):
        for record in data:
            work = self.db.work.Work.one({"_id" : "urn:uuid:%s" % record["work_id"]})
            exp = self.db.expression.Expression.one({"_id" : "urn:uuid:%s" % record["item_id"]})

            expressions = work.get("frbr:expression", [])
            eref = mongokit.DBRef("expression", exp["_id"])
            if eref not in expressions:
                expressions.append(eref)
            work["frbr:expression"] = expressions

            works = exp.get("frbr:expressionOf", [])
            wref = mongokit.DBRef("work", work["_id"])
            if wref not in works:
                works.append(wref)
            exp["frbr:expressionOf"] = works

            wtype = self.db.work_types.one({"_id": work["_id"]})
            if wtype["type"] == "text":
                exp["rdf:type"] = [rdf.FRBR.Text]

            #pprint(work)
            work.save()
            exp.save()

    def load_person_links(self, data):
        for record in data:
            work = self.db.work.Work.one({"_id" : "urn:uuid:%s" % record["work_id"]})
            person = self.db.person.Person.one({"_id" : "urn:uuid:%s" % record["person_id"]})

            role = record["role"]
            if role == "author":
                role = "creator"
            role = "frbr:" + role

            roles = work.get(role, [])
            pref = mongokit.DBRef("person", person["_id"])
            if pref not in roles:
                roles.append(pref)
            work[role] = roles

            works = person.get(role+"Of", [])
            wref = mongokit.DBRef("work", work["_id"])
            if wref not in works:
                works.append(wref)
            person[role+"Of"] = works

            work.save()
            person.save()
