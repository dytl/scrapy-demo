import scrapy
from scrapy_playwright.page import PageMethod

class YaohuiSpider(scrapy.Spider):
    name = 'yaozh_test'
    allowed_domains = ['yaozh.com']
    start_urls = ['https://qx.yaozh.com/zgqxss/list']

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                headers={
                    'Referer': 'https://qx.yaozh.com',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36',
                },
                meta={
                    "playwright": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_selector", "table.el-table__body", timeout=60000)  # 等待页面表格加载完成
                    ],
                },
                callback=self.parse
            )

    def parse(self, response):
        # 选择表格中的每一行
        rows = response.css('table.el-table__body tbody tr')

        for row in rows:
            # 提取注册证编号链接
            detail_url = row.css('td:nth-child(1) div.cell a::attr(href)').get()
            if detail_url:
                detail_url = response.urljoin(detail_url)  # 处理相对路径
                yield scrapy.Request(
                    detail_url,
                    headers={
                        'Referer': response.url,
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36',
                    },
                    meta={
                        "playwright": True,
                        "playwright_page_methods": [
                            PageMethod("wait_for_selector", "div.right-list", timeout=60000)  # 等待详细信息加载完成
                        ],
                    },
                    callback=self.parse_detail
                )

    def parse_detail(self, response):
        # 获取所有表格行
        rows = response.css('table.tb-t tr')

        item = {}
        for row in rows:
            # 提取每一行的表头（例如：注册证编号，注册人名称等）
            header = row.css('td:first-child::text').get().strip()
            # 提取对应的表格内容
            content = row.css('td div.td-line5::text').get()
            if content:
                content = content.strip()

            # 添加到 item 中
            if header:
                item[header] = content

        # 输出抓取的数据
        yield item
