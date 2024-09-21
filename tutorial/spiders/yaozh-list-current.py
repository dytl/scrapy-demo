import scrapy
from scrapy_playwright.page import PageMethod

# 分页已好
class YaohuiSpider(scrapy.Spider):
    name = 'yaohui_spider_next2'
    allowed_domains = ['yaozh.com']
    start_urls = ['https://qx.yaozh.com/zgqxss/list?page=1']  # 初始页码

    # 爬取条目数限制
    item_count_limit = 80
    item_count = 0

    # 保存页面
    saved_page_file = 'saved_page.txt'

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
            if self.item_count >= self.item_count_limit:
                self.logger.info('已达到条目数限制。')
                return  # 达到条目限制，停止爬取

            # 抓取每一列的数据，组装数据
            item = {
                '注册证编号:': row.css('td:nth-child(1) div.cell a::text').get(),  # 第一列中的链接文本
            }
            self.item_count += 1
            # 返回每一行的数据
            yield item

        # 查找当前活动页码
        current_page_element = response.css('ul.el-pager li.number.active')
        if current_page_element:
            current_page = current_page_element.css('::text').get()
            if current_page:
                current_page = int(current_page)

                # 查找下一个页码
                page_numbers = response.css('ul.el-pager li.number')
                next_page_number = None
                for page in page_numbers:
                    page_number_text = page.css('::text').get()
                    if page_number_text:
                        page_number = int(page_number_text)
                        if page_number > current_page:
                            next_page_number = page_number
                            break

                if next_page_number:
                    next_page_selector = f'ul.el-pager li.number:has-text("{next_page_number}")'
                    self.logger.info(
                        f'正在获取第 {next_page_number} 页，URL: https://qx.yaozh.com/zgqxss/list?page={next_page_number}')

                    # 保存当前页码
                    self.save_current_page(current_page+','+next_page_number)

                    yield scrapy.Request(
                        f'https://qx.yaozh.com/zgqxss/list?page={next_page_number}',
                        meta={
                            "playwright": True,
                            "playwright_page_methods": [
                                PageMethod("click", next_page_selector),  # 点击数字页码
                                PageMethod("wait_for_selector", "table.el-table__body", timeout=60000)  # 等待新页面内容加载完成
                            ],
                        },
                        callback=self.parse
                    )
                else:
                    self.logger.info("没有更多页面。")
            else:
                self.logger.error("未找到当前页码的文本。")
        else:
            self.logger.error("未找到当前活动页码元素。")

    def get_saved_page(self):
        try:
            with open(self.saved_page_file, 'r') as file:
                return int(file.read().strip())
        except FileNotFoundError:
            return 0
        except ValueError:
            return 0

    def save_current_page(self, page_number):
        with open(self.saved_page_file, 'w') as file:
            file.write(str(page_number))
