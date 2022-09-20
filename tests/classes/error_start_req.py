class SpiderWithoutForLoop(BaseSpider):
    name = 'something_spider'

    def __init__(self):
        self.some = 'something'

    def start_requests(self):
        yield Request(url=url, callback=self.callback, meta={})