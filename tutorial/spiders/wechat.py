import scrapy
from scrapy_playwright.page import PageMethod

class WechatSpider(scrapy.Spider):
    name = 'wechat'
    allowed_domains = ['mp.weixin.qq.com']
    start_urls = [
        'https://mp.weixin.qq.com/s?__biz=MjM5NjU1MjczNA==&mid=2651535957&idx=1&sn=d86873620738a5b939ffa871f99a00cd&chksm=bcb1e1268a4443c54d2b88384ee45a772e2ed8ff78a2bd62bb0059c35e28830cc70ab12fa452&scene=27#wechat_redirect'
    ]

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta={
                    "playwright": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_selector","div#js_content")
                    ],
                },
            )

    def parse(self, response):
        title = response.xpath('//h1/text()').get()
        content = response.xpath('//div[@id="js_content"]//text()').getall()
        content = ''.join(content).strip()

        yield {
            'title': title,
            'content': content
        }