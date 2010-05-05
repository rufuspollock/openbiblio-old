'''Support for indexing and searching texts using xapian.

Architecture
============

For information on theoretical structure of Xapain see:
http://xapian.org/docs/intro_ir.html

For basic demo python code see: http://xapian.org/docs/bindings/python/

For helpful example of using Xapian in python (including metadata, add_post
etc) see:

  * http://www.thesamet.com/blog/2007/02/04/pumping-up-your-applications-with-xapian-full-text-search/
  * http://www.rkblog.rk.edu.pl/w/p/xapian-python/


  * What is our atomization level. I.e. what are 'documents' we index? Is it:

      * righ now, we index 
            * per work, adding as terms all the related persons.
            * per person, adding all the aka's as synonyms and all works as
              terms

TODO:
    * add metadata as dates, tags
    * items!
    * reindexing last modified records in a cronjob
    * creating some hook to index when saving a work/person
    * related docs:
        xapian provides "related documents", we could integrate it on the web
         interface. (see also... when visiting an author's page)
    * special queries/views

DEPLOYMENT:
    * once installed, run index_all_works() and index_all_persons()



'''
import os
import re

import xapian
import pdw

# keys for document values
ITEM_ID = 0
ITEM_MODEL = 1
LINE_NO = 2
ITEM_URL = 3
ITEM_EXTRAS = 4
WORD_RE = re.compile(r"\\w{1,32}", re.U)
DEFAULT_SEARCH_FLAGS = (
            xapian.QueryParser.FLAG_BOOLEAN |
            xapian.QueryParser.FLAG_AUTO_MULTIWORD_SYNONYMS |
            xapian.QueryParser.FLAG_LOVEHATE 
            )

class InvalidArgumentError:
    pass

class SearchIndex(object):
    def __init__(self, index_dir):
        self.index_dir = index_dir
        self.xapiandb = xapian.WritableDatabase(index_dir, xapian.DB_CREATE_OR_OPEN)
        flintlock = os.path.join(self.index_dir, 'flintlock') 
        if os.path.exists(flintlock): 
            os.unlink(flintlock) 
        self.stemmer = xapian.Stem('en')

    @classmethod
    def config_index_dir(self):
        '''Get the search index directory specified in the config.'''
        from pylons import config
        index_dir = config['search_index_dir']
        return index_dir

    @classmethod
    def default_index(self):
        '''Return a SearchIndex instance initialized with the path specified in
        the configuration file.
        '''
        index_dir = self.config_index_dir()
        if not os.path.exists(index_dir):
            os.makedirs(index_dir)
        return SearchIndex(index_dir)

    def remove_item(self, item_id):
        id_term = self._make_id_term(item_id)
        database = self.xapiandb
        database.delete_document(id_term)

    def search(self, query_string, offset=0, numresults=50):
        '''searches in all fields and gives 50 results per default
        
        examples:
            homer -clarke type:text
            alice wonderland name:carroll

            '''
        enquire = xapian.Enquire(self.xapiandb)
        qp = xapian.QueryParser()
        # prefixes allow us to search with keywords as:
        # alice wonderland type:work pd:1.0
        qp.add_prefix("name", "NA")
        qp.add_prefix("title", "ZT")
        qp.add_prefix("tag", "TA")
        qp.add_prefix("type", "TY")
        qp.set_stemmer(self.stemmer)
        qp.set_database(self.xapiandb)
        qp.set_stemming_strategy(xapian.QueryParser.STEM_SOME)
        query = qp.parse_query(query_string,DEFAULT_SEARCH_FLAGS)
        enquire.set_query(query)
        matches = enquire.get_mset(offset, numresults)

        return matches

    @classmethod
    def print_matches(self, matches):
        # Display the results.
        msg = '%i results found.' % matches.get_matches_estimated()
        msg += 'Results 1-%i:' % matches.size()

        for m in matches:
            msg += '\n'
            msg += '%i: %i%% docid=%i' % (m.rank + 1, m.percent, m.docid)
            msg += '\n'
            msg += m.document.get_data()
            msg += '\n'
        return msg

    def index_person(self,person,deep=True):
        '''takes a model.Person object and indexes it'''

        if person == None:
            print "person not on database. spkipping to next person"
            return

        if deep == False:
            # if we are just loading a person because is related to some work
            if self.xapiandb.term_exists('ID'+str(person.id)):
                print person.name, 'already on database'
                return 

        person_doc = xapian.Document()
        personindexer = xapian.TermGenerator()
        personindexer.set_document(person_doc)
        personindexer.set_stemmer(self.stemmer)

        personindexer.index_text('person',1,'TY')

        id_term = 'ID'+str(person.id)
        person_doc.add_term(id_term)
        try: 

            self.xapiandb.replace_document(id_term, person_doc)

            return person_doc
        except:
            print "some error happenned when creating index for person "
            print person.id, person.name

    
    def index_person_list(self,personlist):
        '''
        from a persons query list, reindexes all persons
        '''
        count = 0
        for person in personlist:
            count += 1
            print count
            try:
                person_doc = self.index_person(person)
            except InvalidArgumentError:
                print 'there has been an error with ', person.name, person.id
                print InvalidArgumentError
        self.xapiandb.flush()

    def index_work_list(self,worklist):
        '''
        from a works query list, reindexes all works
        '''
        count = 0
        for work in worklist:
            if str(count).endswith('000'):
                self.xapiandb.flush()

            count += 1
            #print count
            try:
                work_doc = self.index_work(work)
            except InvalidArgumentError:
                pass
        self.xapiandb.flush()

    def index_work(self,work=None):
        """Gets a work object (model.Work()) and returns
        a Xapian document representing it and
        a unique article identifier."""
        indexer = xapian.TermGenerator()
        indexer.set_stemmer(self.stemmer)

        indexer.set_document(doc)
        indexer.index_text('work',2,'TY')
        # this one is the pylons id, to retrieve the 
        # real object whenever we please:
        doc.add_value(ITEM_ID, str(work.id))
        doc.add_value(ITEM_MODEL, u'work')
        # any easier way of getting a list of 
        # works/items/persons together than to store the url as a key?
        doc.add_value(ITEM_URL, str(work.url)) 
        # some extra info to enrich the engine
        if persons:
            extras = ' by '+', '.join(persons)
        if work.date:
            extras += ' - '+str(work.date)
        if extras:
            doc.add_value(ITEM_EXTRAS, extras.encode('utf8'))

        # now we update the doc using the id as key.
        # if the work is not there, it will be created

        self.xapiandb.replace_document(work_id_term, doc)

        return doc

    def result_list(self, search):
        '''makes a search and renders a nice list 
        ready for the html template engine.
        we have indexed the url value and the type of object( work, person or
        item) so this shouldnt be hard...'''
        results = self.search(search)
        out_list = [] #the dict we will return with enough info to render a list
        for match in results:
            doc = match.document
            name = doc.get_data()
            terms = []
            pd = 0.1
            for term in doc.termlist():
                if term.term.startswith('ST'):
                    pd = term.term[2:]


            try:
                match = { 'url': doc.get_value(3),
                         'name': name,
                         'type': doc.get_value(1),
                         'extra': doc.get_value(4),
                         'prob': match.percent,
                         'terms':terms,
                         'pd': pd,
                        }
            except:
                self.xapiandb.flush()


            out_list.append(match)
        return out_list, results.size()

    def index_range(self,start,end=None):
        '''index a number of records from the database.

        usage: index_range(100,200)
        '''
        if end==None:
            end = start+5000

        worklist = pdw.model.Session.query(pdw.model.Work)[start:end].all()
        self.index_work_list(worklist)
        self.xapiandb.flush()
        pdw.model.Session.remove()

    def index_all_works(self, start=0, model='Work'):
        '''
        takes chunks of 500 works  from the database
        and reindexes them, along with their appended 
        Persons
        
        usage: index_all(35000) 
        for indexing all records starting from the 35000 till the end
        '''
        end = float(pdw.model.Work.query.count())
        
        stop = start
        while stop < end: 
            print('%s (%s%%)') % (stop, stop/end*100)
            if stop+500>end:
                self.index_range(stop,end)
                stop = end
            else:
                self.index_range(stop,stop+500)
                stop +=500
                self.xapiandb.flush()

    def index_all_persons(self,start=0,end=None):
        ''' with this command we can index all the remaining persons
        usage: 
            index_all_persons(300) :: to index from 0 to 300
        '''


        if end == None:
            end = float(pdw.model.Person.query.count())
            print "will index from ", start, " to ", end, ": ", end-start

        stop = start
        while stop<end: 
            print stop
            if stop+500>end:
                self.index_person_range(stop,end)
                stop = end
            else:
                self.index_person_range(stop,stop+500)
                stop +=500

                print stop/end*100, " %"
                self.xapiandb.flush()
        


    def index_person_range(self,start,end=None):
        '''index a number of records from the database.

        usage: index_range(100,200)
        '''
        if end==None:
            end = start+5000

        person_list = pdw.model.Session.query(pdw.model.Person)[start:end].all()

        for index, person in enumerate(person_list):
            self.index_person(person)
            if str(index).endswith('00'):

                self.xapiandb.flush()
        pdw.model.Session.remove()

















