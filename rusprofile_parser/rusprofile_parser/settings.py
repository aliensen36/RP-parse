
DOWNLOADER_MIDDLEWARES = {
    'rusprofile_parser.middlewares.HandleHttpErrorMiddleware': 543,
    # 'rusprofile_parser.middlewares.SeleniumMiddleware': 544,
}


BOT_NAME = "rusprofile_parser"

SPIDER_MODULES = ["rusprofile_parser.spiders"]
NEWSPIDER_MODULE = "rusprofile_parser.spiders"

# Obey robots.txt rules
ROBOTSTXT_OBEY = False


# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"


ITEM_PIPELINES = {
   'rusprofile_parser.pipelines.RusprofileParserPipeline': 300,
}
