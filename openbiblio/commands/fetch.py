from openbiblio.commands import Command
from datetime import datetime
import logging
import swiss
import os

def _exists(filename):
	try:
		os.stat(filename)
		return True
	except OSError:
		return False
		
class Fetch(Command):
	summary = "Fetch Dataset(s)"
	usage = "config.ini dataset [dataset2 [dataset3 [...]]]"
	parser = Command.standard_parser(verbose=False)
	parser.add_option("-c", "--config",
		dest="config_file",
		default="development.ini",
		help="Configuration File"
	)
	def command(self):
		self.parse_config(self.options.config_file)
		self.cache = swiss.Cache(self.config.get("cache_dir", "data"))
		self.log = logging.getLogger("fetch")
		for arg in self.args:
			self.fetch(arg)
	def fetch(self, dataset):
		url = self.config.get("%s" % (dataset,), None)
		if url is None:
			self.log.error("no download url for dataset %s in config file" % (dataset,))
			return
		archive = self.cache.filepath(url)
		if not _exists(archive) or self.options.force:
			self.log.info("downloading %s" % (url,))
			start = datetime.now()
			self.cache.retrieve(url)
			end = datetime.now()
			self.log.info("%s: %s bytes in %s" % (archive, os.stat(archive).st_size, end-start))
