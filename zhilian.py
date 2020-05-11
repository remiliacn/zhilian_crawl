from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import requests, re, json, time



class zhilianCrawl:
    def __init__(self, driverPath, retry=3):
        print("请保证爬虫的时候不要最小化浏览器")
        self.retry = retry
        time.sleep(3)
        self.options = webdriver.ChromeOptions()
        #Pretend to be an actual machine and an actual user visiting the site.
        self.options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.options.add_experimental_option('useAutomationExtension', False)
        self.options.add_argument('log-level=3')

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36',
            'Host': 'sou.zhaopin.com',
            'Referer': 'https://sou.zhaopin.com/?jl=530&in=100030000&kw=C++&kt=3',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Origin' : 'https://sou.zhaopin.com',
            'Sec-Fetch-Dest' : 'empty',
            'Sec-Fetch-Mode' : 'cors',
            'Sec-Fetch-Site' : 'same-site'
        }

        self.driver = webdriver.Chrome(options=self.options, executable_path=driverPath)
        #use headers that pretend to be a human user.
        self.driver.execute_cdp_cmd("Network.setExtraHTTPHeaders", {"headers": self.headers})
        #hide webDriver property to pass the anti-crawling mechanism from zhilian.com
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                  get: () => undefined
                })
              """
        })

    def searchResult(self, queryIn : str):
        result = ''
        self.driver.get(f"https://sou.zhaopin.com/?jl=530&kw={queryIn}&kt=3")
        company = self.driver.find_elements_by_xpath('//*[@id="listContent"]/div/div/a/div[1]/div[2]/a')
        if not company:
            i = 0
            while i < self.retry:
                try:
                    WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located((By.XPATH, '//*[@id="listContent"]/div/div/a/div[1]/div[2]/a')))
                    break

                except TimeoutException:
                    print(f"刷新重试……({i + 1}/{self.retry})")
                    self.driver.refresh()

            company = self.driver.find_elements_by_xpath('//*[@id="listContent"]/div/div/a/div[1]/div[2]/a')
            if not company:
                return f'未找到关键字为{queryIn}的职位信息'

        print("信息获取成功！整理中……")
        job_title = self.driver.find_elements_by_xpath('//*[@id="listContent"]/div/div/a/div[1]/div[1]/span[1]')
        salary = self.driver.find_elements_by_xpath('//*[@id="listContent"]/div/div/a/div[2]/div[1]/p')
        experience = self.driver.find_elements_by_xpath('//*[@id="listContent"]/div/div/a/div[2]/div[1]/ul/li[2]')

        for i in range(len(job_title)):
            result += (f'===公司名称：{company[i].text}===\n'
                       f'* 岗位名称：{job_title[i].text}\n' +
                       f'* 薪水：{salary[i].text}\n')

            experience_text = '* 要求经验：' + experience[i].text.replace('\r', '').replace('\n', '') + '\n'
            result += experience_text + '\n'

        self.driver.close()
        return result

    def zhilian(self):
        page = requests.get('https://www.zhaopin.com/beijing/')
        page.encoding = 'utf-8'
        data = re.findall(r'<script>__INITIAL_STATE__=(.*?)</script>', page.text)[0]
        json_data = json.loads(data)

        """
        jobID : int
        :param
        {
            IT = 0
            服务 = 1
            汽车/制造 = 2
            贸易/零售 = 3
            房地产 = 4
            医疗化工 = 5
            消费品 = 6
            文化传媒 = 7
            金融 = 8
            其他 = 9
        }
        """
        jobID = 0
        IT_Job_List = json_data['pageData']['requestData']['hotJob'][jobID]['list']

        for job in IT_Job_List:
            print(f"===公司名称：{job['orgName']}:===\n"
                  f"岗位名称：{job['jobName']}\n"
                  f"招聘人数：{job['fillup']}\n"
                  f"工作代码：{job['jobNumber']}\n"
                  f"公司代码：{job['orgNumber']}\n"
                  f"薪水区间：{job['salary']}\n"
                  f"详细信息URL：{job['orgUrl']}")

if __name__ == '__main__':
    query = input('请输入要查询的职位')
    lian = zhilianCrawl('E:\Coding\Python\Driver\chromedriver.exe')
    print(lian.searchResult(query))
    exit(1)
