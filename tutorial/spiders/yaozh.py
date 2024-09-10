import scrapy
from scrapy_playwright.page import PageMethod

class YaozhSpider(scrapy.Spider):
    name = 'yaozh_spider'
    allowed_domains = ['yaozh.com']
    start_urls = ['https://qx.yaozh.com/login']

    def start_requests(self):
        login_url = 'https://qx.yaozh.com/login'
        # 使用 Playwright 模拟登录
        yield scrapy.Request(
            login_url,
            meta={
                "playwright": True,
                "playwright_page_methods": [
                    # 等待用户名输入框加载
                    PageMethod("wait_for_selector", "input[name='name']"),
                    # 输入用户名
                    PageMethod("fill", "input[name='name']", "yuanmaliliang"),
                    # 输入密码
                    PageMethod("fill", "input[name='pwd']", "Yuanma@2024"),
                    # 点击登录按钮
                    PageMethod("click", "button[type='submit']"),
                    # 等待页面重定向
                    #PageMethod("wait_for_selector", "div#app"),
                    # 等待页面加载
                    PageMethod("wait_for_load_state", 'networkidle'),
                ],
                #"playwright_context": "new",  # 保持新的上下文
                "playwright_include_page": True  # 保持页面对象，以便后续跳转
            },
            callback=self.after_login
        )

    async def after_login(self, response):
        # 登录成功后，跳转到目标数据页面
        page = response.meta["playwright_page"]

        # 处理登录成功后的弹窗或提示框
        try:
            # 等待提示框出现并点击确认按钮
            await page.wait_for_selector('button.confirm-button-selector', timeout=30000)
            await page.click('button.confirm-button-selector')
        except Exception as e:
            self.logger.error(f"Error handling the confirmation popup: {e}")

        target_url = 'https://qx.yaozh.com/zgqxss/list'


        # 手动跳转到目标页面
        await page.goto(target_url)

        # 从目标页面提取数据
        response = await page.content()
        self.parse_list(response)

        # yield scrapy.Request(
        #     target_url,
        #     meta={
        #         "playwright": True,
        #         "playwright_page": page,  # 使用登录后的页面对象
        #         "playwright_page_methods": [
        #             PageMethod("wait_for_selector", "div.el-table__body-wrapper", timeout=60000)  # 等待表格出现
        #         ],
        #     },
        #     callback=self.parse_list
        # )


    def parse_list(self, response):
        # 解析第一页内容
        rows = response.css('div.search-body-content tbody tr')
        for row in rows:
            name = row.css('td.el-table_1_column_2 span').get()
            location = row.css('td.el-table_1_column_3 span').get()
            approval_date = row.css('td.el-table_1_column_4 span').get()

            yield {
                'name': name,
                'location': location,
                'approval_date': approval_date,
            }

