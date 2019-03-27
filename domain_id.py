import requests
import json
from pyquery import PyQuery as pq
import time
import multiprocessing as mp


class ProxiesDB(object):
    def __init__(self):
        self.Proxies = None
        self.Proxies_list = []

    def get_proxies_func(self):
        if not self.Proxies_list:
            print('\033[1;31;48m{------>开始收集代理ip<------}\033[0m')
            ip_port_json = requests.get('https://dev.kdlapi.com/api/getproxy/?orderid=975144938571448&num=20'
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


class EmailMainSpider(object):
    def __init__(self, header, b_year, e_year, domain_name, domain_range, pdb):
        self.Domain_name = domain_name

        self.Header = header
        self.B_year = b_year
        self.E_year = e_year
        self.Domain_range = domain_range

        self.last_id_list = ['init']
        self.Proxies = None
        self.Flag = 0
        self.page_num = 1
        self.page_size = 100

        self.cheat_url = 'http://qikan.cqvip.com/CheckRequest/IsVerificationPass'
        self.main_url = 'http://qikan.cqvip.com/Search/SearchList'

        self.Proxies_db = pdb
        self.cheat_server()

    def change_ip(self):
        self.Proxies = self.Proxies_db.get_proxies_func()

    def create_post_data(self):
        keywords = 'searchParamModel='
        post_data = {'ObjectType': 1, 'SearchKeyList': [
            {'FieldIdentifier': 'Z', 'SearchKey': 'com', 'PreLogicalOperator': '', 'IsExact': '0'},
            {'FieldIdentifier': 'Z', 'SearchKey': 'cn', 'PreLogicalOperator': 'OR', 'IsExact': '0'},
            {'FieldIdentifier': 'S', 'SearchKey': 'net', 'PreLogicalOperator': 'OR', 'IsExact': '0'}],
                     'SearchExpression': '',
                     'BeginYear': '{}'.format(self.B_year),
                     'EndYear': '{}'.format(self.E_year),
                     'DomainRange': '{}'.format(self.Domain_range),
                     'PageSize': '{}'.format(self.page_size),
                     'PageNum': '{}'.format(self.page_num),
                     'JournalRange': '',
                     'Sort': '0', 'ClusterFilter': '',
                     'SType': '', 'StrIds': '', 'UpdateTimeType': '', 'ClusterUseType': 'Article', 'IsNoteHistory': 1,
                     'AdvShowTitle': '作者简介=com+OR+作者简介=cn+OR+机构=net', 'ObjectId': '', 'ObjectSearchType': '0',
                     'ChineseEnglishExtend': '0', 'SynonymExtend': '0', 'ShowTotalCount': '0',
                     'AdvTabGuid': '820eb83a-22f9-6dfb-f961-00be7cc8c9da'}
        keyword_post_data = keywords + json.dumps(post_data)
        return keyword_post_data

    def cheat_server(self):
        print('\033[1;31;48m{--->开始欺骗服务器操作<---}\033[0m')
        try:
            response = requests.post(url=self.cheat_url, data='verificationCode=', headers=self.Header,
                                     allow_redirects=False, timeout=15, proxies=self.Proxies)
            response.close()
            response.json()

            print('\033[1;33;48m{->cheat success!!!<-}\033[0m')
        except Exception as e:
            print(e)
            print('\033[1;31;48m{------>cheat error!!!换IP后重试<------}\033[0m')
            self.change_ip()
            self.cheat_server()

    def get_html(self):
        try:
            post_data = self.create_post_data()
            response = requests.post(self.main_url, headers=self.Header, data=post_data, allow_redirects=False,
                                     timeout=15, proxies=self.Proxies)
            html = response.text
            response.close()
            return html
        except Exception as e:
            print(e)
            print('get html error!!!')
            self.change_ip()
            self.cheat_server()
            self.get_html()

    def run(self):
        id_list = []
        while id_list != self.last_id_list:
            try:
                pass_id_list = self.last_id_list
                self.last_id_list = id_list
                html = self.get_html()
                doc = pq(html)
                id_list_exist = doc('.layui-col-xs5')
                if id_list_exist:
                    id_list = [one.attr('data-id')
                               for one in doc('.search-result-list .table-list tbody tr input').items()]
                    if len(id_list) > 0:
                        with open('{0}_{1}_id.txt'.format(self.Domain_name, self.Domain_range), 'a+') as f:
                            f.write(json.dumps(id_list) + '\n')
                        print('\033[1;34;48m \n成功获取领域:{0},{1}年的第{2}页文章id数{3}个 \033[0m'.format(
                            self.Domain_name, self.E_year, self.page_num, len(id_list)))
                        self.Flag = 0
                        self.page_num = self.page_num + 1
                        time.sleep(3)
                    else:
                        self.last_id_list = id_list
                else:
                    id_list = self.last_id_list
                    self.last_id_list = pass_id_list
                    print('\033[1;31;48m *>error!!!领域:{0}，{1}年的文章第{2}页获取失败,重新获取<* \033[0m'.format(
                        self.Domain_name, self.E_year, self.page_num))
                    if self.Flag < 3:
                        self.Flag += 1
                        self.change_ip()
                        self.cheat_server()
                        time.sleep(3)
                    else:
                        error_info = '领域:{0},{1}年的文章，第{2}页获取失败已经重试3次'.format(
                            self.Domain_name, self.E_year, self.page_num)
                        print('\033[1;36;48m *>error!!!{0}<* \033[0m'.format(error_info))
                        with open('log.txt', 'a+') as log:
                            log.write(error_info + '\n')
                        self.page_num += 1
            except Exception as e:
                print(e)
                print('\033[1;31;48m *>get id list error!!!<* \033[0m')
                self.change_ip()
                self.cheat_server()
        print(self.Domain_name, self.E_year, 'done!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')


def get_data(headers, b_y, e_y, p_db):
    domains = {
        '生物学': 9, '天文地球': 10, '化学工程': 12, '矿业工程': 13, '石油与天然气工程': 14, '冶金工程': 15, '金属学及工艺': 16,
        '机械工程': 17, '动力工程及工程热物理': 18, '电子电信': 19, '电气工程': 20, '自动化与计算机技术': 21, '建筑科学': 22,
        '水利工程': 23, '轻工技术与工程': 25, '交通运输工程': 26, '航空宇航科学技术': 27, '环境科学与工程': 28, '核科学技术': 29,
        '医药卫生': 30, '农业科学': 35, '一般工业技术': 257, '自然科学总论': 266, '理学': 267, '兵器科学与技术': 268,
    }
    for key in domains:
        spider = EmailMainSpider(header=headers, b_year=b_y, e_year=e_y, domain_name=key,
                                 domain_range=domains[key], pdb=p_db)
        spider.run()


if __name__ == '__main__':
    Headers = {
        'Host': 'qikan.cqvip.com',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'User-Agent': '360spider (http://webscan.360.cn)',
        'Accept-Language': 'zh-CN,en-US;q=0.8',
    }

    proxies_db = ProxiesDB()
    for year in [2015, 2016, 2017, 2018, 2019]:
        pool = mp.Process(target=get_data, args=(Headers, year, year, proxies_db))
        pool.start()
        print('进程--{}--启动'.format(str(year)))
        time.sleep(5)
