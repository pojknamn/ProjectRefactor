def start_requests(self):
    for url in self.start_urls:
        initial_url = url
        yield Request(url=url, callback=self.parse, dont_filter=True, meta={'initial_url': initial_url})