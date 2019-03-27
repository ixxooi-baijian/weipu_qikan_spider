from pyquery import PyQuery as pq
import requests
import json
import re
import time
import multiprocessing as mp


class ProxiesDB(object):
    def __init__(self):
        self.Proxies = None
        self.Proxies_list = []

    def get_proxies_func(self):
        if not self.Proxies_list:
            print('\033[1;31;48m{------>开始收集代理ip<------}\033[0m')
            ip_port_json = requests.get('https://dev.kdlapi.com/api/getproxy/?orderid=975144938571448&num=50'
                                        '&b_pcchrome=1&b_pcie=1&b_pcff=1&protocol=1&method=2&an_an=1&an_ha=1'
                                        '&quality=1&sort=1&format=json&sep=1')
            ip_port_json.close()
            for ip_port in ip_port_json.json()['data']['proxy_list']:
                proxies = {
                    'http': ip_port,
                    'https': ip_port,
                }
                self.Proxies_list.append(proxies)
            self.Proxies = self.Proxies_list.pop()
            print(self.Proxies)
            return self.Proxies
        else:
            print('{------>开始更换ip:')
            self.Proxies = self.Proxies_list.pop()
            print(self.Proxies)
            return self.Proxies


class IdEmailSpider(object):
    def __init__(self, pdb):
        self.Pdb = pdb
        self.Proxies = None
        self.Headers = {
            'host': 'm.qikan.cqvip.com',
            'origin': 'http://m.qikan.cqvip.com',
            'User-Agent': '360spider (http://webscan.360.cn)',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': 'http://m.qikan.cqvip.com',
        }

    def main_spider(self, article_id):
        url = 'http://lib.cqvip.com/Qikan/Article/Detail?id={}&from=Qikan_Search_Index'.format(article_id)
        try:
            res = requests.get(url, headers=self.Headers, allow_redirects=False, timeout=10, proxies=self.Proxies)
            html = res.content
            res.close()
            doc = pq(html)
            result = doc('body .others').text()
            return result
        except Exception as e:
            print(e)
            return 'error'

    @staticmethod
    def search_email(text):
        res = re.findall('[\w]+@[\w\s]+[\w\.\．]+[\w\.\．]+[\w]+', text, re.ASCII)
        return res

    def change_ip(self):
        self.Proxies = self.Pdb.get_proxies_func()

    def main_process(self, domain_name, domain):
        with open('{0}_{1}_id.txt'.format(domain_name, domain), 'r') as lines:
            for index_list, one_id_list in enumerate(lines):
                for index_list_position, ID in enumerate(json.loads(one_id_list)):
                    text = self.main_spider(ID)

                    count = 0
                    while not text or text == 'error':
                        if count <= 3:
                            count += 1
                            self.change_ip()
                            text = self.main_spider(ID)

                        else:
                            error_info = '领域:{0} ID:{1}的文章，获取失败已经重试3次'.format(
                                domain_name, ID)
                            print('\033[1;36;48m *>error!!!{0}<* \033[0m'.format(error_info))
                            with open('email/log.txt', 'a+') as log:
                                log.write(error_info + '\r\n')
                            break
                    res = self.search_email(text)
                    if res:
                        with open('email/{0}_{1}_email.txt'.format(domain_name, domain), 'a+') as txt_data:
                            for one in res:
                                txt_data.write(one + '\r\n')
                                print('领域{0}第{1}行列表第{2}位邮箱数据，邮箱:{3}'.format(domain_name, index_list, index_list_position, one))
                    else:
                        print(text)
                        print('领域{0}第{1}行列表第{2}位数据无法处理'.format(domain_name, index_list, index_list_position))


if __name__ == '__main__':
    print('中途中断可记录index号，然后重新爬取在id_title_qikan.txt删除行号为index号前所有的数据就可以。')

    domains = {
        '生物学': 9, '天文地球': 10, '化学工程': 12, '矿业工程': 13, '石油与天然气工程': 14, '冶金工程': 15, '金属学及工艺': 16,
        '机械工程': 17, '动力工程及工程热物理': 18, '电子电信': 19, '电气工程': 20, '自动化与计算机技术': 21, '建筑科学': 22,
        '水利工程': 23, '轻工技术与工程': 25, '交通运输工程': 26, '航空宇航科学技术': 27, '环境科学与工程': 28, '核科学技术': 29,
        '医药卫生': 30, '农业科学': 35, '一般工业技术': 257, '自然科学总论': 266, '理学': 267, '兵器科学与技术': 268,
    }

    proxies_db = ProxiesDB()
    spider = IdEmailSpider(proxies_db)
    for key in domains:
        pool = mp.Process(target=spider.main_process, args=(key, domains[key]))
        print('进程--{}--启动'.format(key))
        pool.start()
        time.sleep(3)

