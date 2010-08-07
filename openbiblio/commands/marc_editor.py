from openbiblio.commands import Command
import logging
import pymarc

class Editor(Command):
    summary = "Extract records from MARC file"
    usage = "[options] config.ini file.mrc"
    parser = Command.standard_parser(verbose=False)
    parser.add_option("-r", "--records",
                      dest="records",
                      default="",
                      help="Comma separated list of records to extract",
                      )
    parser.add_option("-o", "--output",
                      dest="output",
                      default=None,
                      help="Output MARC21 file")
    parser.add_option("-a", "--append",
                      dest="append",
                      default=False,
                      action="store_true",
                      help="Append rather than overwrite output file")
    parser.add_option("-c", "--count",
                      dest="count",
                      default=False,
                      action="store_true",
                      help="Simply count the number of records in the file")

    def command(self):
        self.log = logging.getLogger("marc_editor")
        reader = pymarc.reader.MARCReader(file(self.args[0]))
        records = []
        for recspec in self.options.records.split(","):
            if not recspec: continue
            if "-" in recspec:
                start, end = [int(x) for x in recspec.split("-")]
                records.extend(range(start, end+1))
            else:
                records.append(int(recspec))
        if not records and not self.options.count: records = range(10)

        if self.options.output:
            if self.options.append:
                ofp = mode = "a"
            else:
                mode = "w"
            ofp = open(self.options.output, mode)
            writer = pymarc.writer.MARCWriter(ofp)
            def output(record):
                writer.write(record)
        else:
            def output(record):
                print record

        last = max(records) if records else -1
        i=0
        for record in reader:
            if i in records:
                output(record)
            i += 1
            if last >= 0 and i > last:
                break

        if self.options.output:
            ofp.close()
        if self.options.count:
            print i
