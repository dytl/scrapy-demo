import scrapy
from scrapy_playwright.page import PageMethod
import mysql.connector
import json

# 测试跑通！
class YaohuiSpider(scrapy.Spider):
    name = 'yaozh_detail_mysql'
    allowed_domains = ['yaozh.com']
    start_urls = ['https://qx.yaozh.com/zgqxss/list']

    # Initialize database connection
    def __init__(self):
        self.connection = mysql.connector.connect(
            host='39.107.138.72',  # Update with your MySQL host
            user='root',  # Update with your MySQL username
            password='477ba090e70cd6a0',  # Update with your MySQL password
            database='tasksystem'  # Update with your MySQL database name
        )
        self.cursor = self.connection.cursor()

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
                        PageMethod("wait_for_selector", "table.el-table__body", timeout=60000)  # Wait for the table to load
                    ],
                },
                callback=self.parse
            )

    def parse(self, response):
        rows = response.css('table.el-table__body tbody tr')

        for row in rows:
            detail_url = row.css('td:nth-child(1) div.cell a::attr(href)').get()
            if detail_url:
                detail_url = response.urljoin(detail_url)
                yield scrapy.Request(
                    detail_url,
                    headers={
                        'Referer': response.url,
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36',
                    },
                    meta={
                        "playwright": True,
                        "playwright_page_methods": [
                            PageMethod("wait_for_selector", "div.right-list", timeout=60000)  # Wait for details to load
                        ],
                    },
                    callback=self.parse_detail
                )

    def parse_detail(self, response):
        rows = response.css('table.tb-t tr')

        item = {}
        for row in rows:
            # 提取每一行的表头（例如：注册证编号，注册人名称等）
            header = row.css('td:first-child::text').get().strip()
            # 提取对应的表格内容
            content = row.css('td div.td-line5::text').get()
            if content:
                content = content.strip()

            if header and content:
                item[header] = content

        # Write data to MySQL
        self.save_to_db(item)

    # Method to save data to the database
    def save_to_db(self, item):
        # 将 item 转换为 JSON 字符串
        json_str = json.dumps(item)

        # Insert the data into a MySQL table, e.g., 'scraped_data'
        query = """
        INSERT INTO data_instrument_json (jsonstr)
        VALUES (%s)
        """
        # 注意 values 必须是一个元组，所以需要加一个逗号
        values = (json_str,)

        try:
            self.cursor.execute(query, values)
            self.connection.commit()
        except Exception as e:
            self.logger.error(f"保存到数据库时出错: {e}")

    # Close the database connection when the spider is closed
    def close(self, reason):
        self.cursor.close()
        self.connection.close()
