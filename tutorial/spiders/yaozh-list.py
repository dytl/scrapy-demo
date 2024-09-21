import scrapy
from scrapy_playwright.page import PageMethod

class YaohuiSpider(scrapy.Spider):
    name = 'yaohui_spider_list'
    allowed_domains = ['yaozh.com']
    start_urls = ['https://qx.yaozh.com/zgqxss/list']

    # 爬取条目数限制
    item_count_limit = 80
    item_count = 0

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
            )

    def parse(self, response):
        # 选择表格中的每一行
        rows = response.css('table.el-table__body tbody tr')

        for row in rows:
            if self.item_count >= self.item_count_limit:
                return  # 达到条目限制，停止爬取

            # 抓取每一列的数据,组装数据
            item = {
                '注册证编号:': row.css('td:nth-child(1) div.cell a::text').get(),  # 第一列中的链接文本
            }
            self.item_count += 1
            # 返回每一行的数据
            yield item

        # 查找下一页按钮是否可用
        next_page_button = response.css('button.btn-next:not([disabled])')  # 确保按钮未禁用
        if next_page_button and self.item_count < self.item_count_limit:
            # 如果下一页按钮存在且未禁用，点击下一页并等待新页面加载
            yield scrapy.Request(
                response.url,
                headers={
                    'Referer': response.url,
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36',
                },
                meta={
                    "playwright": True,  # 启用 playwright
                    "playwright_page_methods": [
                        PageMethod("click", "button.btn-next"),  # 点击下一页按钮
                        PageMethod("wait_for_selector", "table.el-table__body", timeout=60000)  # 等待新页面内容加载完成
                    ],
                },
                callback=self.parse
            )
