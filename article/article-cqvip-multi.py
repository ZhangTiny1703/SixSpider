# coding=gbk

import requests
from bs4 import BeautifulSoup
import time
import os
import sys
import re
import http.cookiejar as HC
import random
import traceback
import hashlib
import logging
from logging.handlers import TimedRotatingFileHandler

# base_path = os.path.abspath(os.path.join(os.getcwd(), ".."))
base_path = r"E:\文档"

log_fmt = '%(asctime)s\tFile \"%(filename)s\",line %(lineno)s\t%(levelname)s: %(message)s'
formatter = logging.Formatter(log_fmt)

# 控制台log配置
# 默认是sys.stderr
log_console_handler = logging.StreamHandler(sys.stdout)
log_console_handler.setLevel(logging.INFO)
log_console_handler.setFormatter(formatter)

# 文件log配置
log_file_handler = TimedRotatingFileHandler(filename=os.path.join(base_path, r"article\cqvip_run.log"), when="D", interval=1, backupCount=7)
log_file_handler.setLevel(logging.INFO)
log_file_handler.setFormatter(formatter)
log_file_handler.suffix = "%Y-%m-%d_%H-%M.log"
log_file_handler.extMatch = re.compile(r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}.log$")

# log初始化
log = logging.getLogger()
log.setLevel(logging.INFO)
log.addHandler(log_file_handler)
log.addHandler(log_console_handler)


headers = {
    'Accept': 'text/html, */*; q=0.01'
    , 'Accept-Encoding': 'gzip, deflate'
    , 'Accept-Language': 'zh-CN,zh;q=0.9'
    , 'Connection': 'keep-alive'
    , 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
    ,
    'Cookie': 'ASP.NET_SessionId=ns5dkfsbstg53y2tltklz1uf;LIBUSERCOOKIE=Oosn4ui+3LIAcpa/+sCLSLumqrc/XpZlqdxCkoqLXe888frrRhvRzCOVrla0ToPKV6Luj9NWHzwzKC24fAeMx7orTNZjIy9oG5qEoA8nJ4PkLiFK9YMoaeMPT//0+cTP5j3Qyzup711HZRD2teAHC/GYoETE1+D7xlFQ6TytIcsHTyOcxdjlMPZHEJ/nr8eZBxiYxUmkIJvCaCtUKeqiKrzERq/MVLncFbNsmiFRV1LsCaK1a1KMoiSryztwcIm+AyQfGjJ4mccXlSmCk+xuunS/ymN0rANZXV8QEWHWVIhEhSJwhULonh/8ujtw7dCRUchYjtu/N9Q0ks49AX7X6MwH+uvZnyjjx6Qoup6VkLMYn24qH6HN2g==;LIBUSERIDCOOKIE=19028277;LIBUSERNAMECOOKIE=447229719@qq.com;search_isEnable=1;skybug=ea4aa775b9af539f55ca5843428f034b;user_behavior_flag=2bb3cccf-1c24-4c40-805d-9f5082b35071;'
    , 'Host': 'qikan.cqvip.com'
    , 'Origin': 'http://qikan.cqvip.com'
    , 'Referer': 'http://qikan.cqvip.com/Qikan/Search/Advance?from=index'
    ,
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
    , 'X-Requested-With': 'XMLHttpRequest'
}


# 登陆信息
data = {
    'Username': '447229719@qq.com',
    'Password': '33530912'
}

# md5转化密码
m2 = hashlib.md5()
m2.update(data['Password'].encode('utf-8'))
data['Password'] = m2.hexdigest()

# 下载文件存储目录
# file_dir = os.path.join(base_path, "维普网")
cur_day = time.strftime('%Y-%m-%d', time.localtime(time.time()))
if cur_day > '2019-03-01':
    log.info("授权已过期")
    exit()

file_dir = os.path.join(base_path, "维普网", cur_day)
if os.path.exists(file_dir):
    print("目录{}已存在，下载文件中...".format(file_dir))
else:
    print("目录{}不存在，创建该目录...".format(file_dir))
    os.mkdir(file_dir)

# 已下载文件列表-目录形式：标题/标题_首作者/文件目录
file_m = os.path.join(base_path, "维普网目录.txt")
# 本网站目录列表 - 标题_首作者 数组
files_m = []


# 其他目录列表 - 标题 数组
other_list = []

# 文件名列表 - 标题 文件名
download_list = {}

# 请求的全局session
session = requests.Session()
cookie_path = os.path.join(base_path, r"article\article-cqvip-cookie.txt")
# print(cookie_path)


def load_list():
    # 加载自己目录
    files_m.clear()
    for f_file in open(file_m, "r", encoding='utf-8'):
        if len(f_file.split("|*|")) < 2:
            continue
        files_m.append(f_file.split("|*|")[1])
        download_list[f_file.split("|*|")[0]] = f_file.split("|*|")[2].split("\\")[-1]

    # 加载其他目录
    other_list.clear()
    files = os.listdir(base_path)
    for file in files:
        if file.find("目录") > 0 and file != "维普网目录.txt":
            for f_file in open(os.path.join(base_path, file), "r", encoding='utf-8'):
                if len(f_file.split("|*|")) < 2:
                    continue
                other_list.append(f_file.split("|*|")[0])


def login():
    session.cookies = HC.MozillaCookieJar(filename=cookie_path)
    # session.cookies.save()
    #  如果存在cookies文件，则加载，如果不存在则提示
    try:
        session.cookies.load(ignore_discard=True, ignore_expires=True)

        session.get('http://qikan.cqvip.com/', headers=headers)
        session.cookies.save(ignore_discard=True, ignore_expires=True)

        session.get('http://qikan.cqvip.com/Qikan/WebControl/IsViewObject', headers=headers)
        session.cookies.save(ignore_discard=True, ignore_expires=True)

        cookie_str = ""
        for cookie in session.cookies:
            # print(cookie.name, cookie.value)
            cookie_str = cookie_str + cookie.name + "=" + cookie.value + ";"
        # log.info(cookie_str)
        headers['Cookie'] = cookie_str

        r1 = session.get('http://qikan.cqvip.com/RegistLogin/CheckUserIslogin?'+str(random.random())
                         , headers=headers)
        # print(r1.json())
        # 登陆验证
        is_login = r1.json().get('isLogined')
        if is_login:
            log.info('已登录 ...cookie有效')
            return
        else:
            log.info('未登录 ...尝试登陆...')
    except Exception as e:
        log.info('未找到cookies文件')
        log.info(traceback.format_exc())

    # 登陆接口
    login_data = {
        'LoginUserName': data['Username'],
        'LoginUserPassword': data['Password'],
        'LoginType': 'normallogin'
    }
    login_r = session.post('http://qikan.cqvip.com/RegistLogin/Login', data=login_data, headers=headers)
    # print(login_r.json())
    # for cookie_l in login_r.cookies:
    #     print(cookie_l.name, cookie_l.value)
    session.cookies.save(ignore_discard=True, ignore_expires=True)
    log.info('登陆成功 ...保存cookie')


def get_total(key=None):
    if not key:
        log.info('没有设置关键词！！！')
        return

    load_list()
    # 获取搜索列表
    url = 'http://qikan.cqvip.com/Search/SearchList'
    list_data = {
        'searchParamModel': '{"ObjectType":1,"SearchKeyList":[],"SearchExpression":"'+key+'","BeginYear":"2019","EndYear":"2019","JournalRange":"","DomainRange":"","PageSize":"0","PageNum":"1","Sort":"0","ClusterFilter":"","SType":"","StrIds":"","UpdateTimeType":"","ClusterUseType":"Article","IsNoteHistory":1,"AdvShowTitle":"'+key+'","ObjectId":"","ObjectSearchType":"0","ChineseEnglishExtend":"0","SynonymExtend":"0","ShowTotalCount":"0","AdvTabGuid":"9a2c2edb-4c06-8fa0-631c-a1745ab6e81c"}'
    }
    r = session.post(url, data=list_data, headers=headers)
    r.encoding = 'utf-8'
    soup = BeautifulSoup(r.text, 'lxml', from_encoding='utf-8')
    # alinks = soup.find_all(attrs={'target': '_blank'})

    result = soup.select('.search-top .search-result span input')
    # print(result)
    total_str = result[0].attrs['value']
    if total_str:
        log.info("==共找到{}篇文章=========".format(total_str))
        total = int(total_str)
    else:
        log.info("文章总数量没有查找到！！！！".format(total_str))
        exit(0)
    page_size = 20
    page_total = int((total + page_size - 1)/page_size)
    log.info("==每页记录20，共{}页=========".format(page_total))
    for page in range(page_total):
        log.info("开始获取第{}页....".format(page + 1))
        get_list(key, str(page + 1))
    log.info("任务完成 ...")


# 获取搜索列表
def get_list(key=None, page="1"):
    if not key:
        print('没有设置关键词！！！')
        return

    # 获取搜索列表，根据条件检索
    # 年份 BeginYear : "2018", EndYear: "2019"
    # 更新时间 UpdateTimeType ： 1/1个月内 2/三个月内 3/半年内 4/一年内 5/当年内
    url = 'http://qikan.cqvip.com/Search/SearchList'
    list_data = {
        'searchParamModel': '{"ObjectType":1,"SearchKeyList":[],"SearchExpression":"'+key+'","BeginYear":"2019","EndYear":"2019","JournalRange":"","DomainRange":"","PageSize":"0","PageNum":"'+page+'","Sort":"0","ClusterFilter":"","SType":"","StrIds":"","UpdateTimeType":"","ClusterUseType":"Article","IsNoteHistory":1,"AdvShowTitle":"'+key+'","ObjectId":"","ObjectSearchType":"0","ChineseEnglishExtend":"0","SynonymExtend":"0","ShowTotalCount":"0","AdvTabGuid":"9a2c2edb-4c06-8fa0-631c-a1745ab6e81c"}'
    }
    r = session.post(url, data=list_data, headers=headers)
    r.encoding = 'utf-8'
    soup = BeautifulSoup(r.text, 'lxml', from_encoding='utf-8')
    alinks = soup.select('#remark dl')
    if alinks:
        i = 0
        for alink in alinks:
            i = i+1
            # 获取文章名称title
            title = alink.select('dt a[target=_blank]')[0].get_text()
            author = alink.select('dd .author a')[0].get_text()
            article_a = alink.select('.article-source a')
            log.info("{},{},{},{}".format(i, title, author, article_a))

            # 去掉包含关键字的题目
            if_down = True
            key_ignore = ["总目次", "索引", "总目录"]
            for key_i in key_ignore:
                if key_i in title:
                    log.info('\t当前文章标题包含关键字 {} ，已忽略下载'.format(key_i))
                    if_down = False
                    break

            if not if_down:
                continue

            # 相同网站文件重复去重-标题名加作者
            if title+"_"+author in files_m:
                log.info('\t文件已存在当前网站目录列表 ... {}'.format(os.path.join(file_dir, title)))
                continue
            # 不同网站重复去重-根据标题
            if title in other_list:
                log.info('\t文件已存在其他网站目录列表 ... {}'.format(os.path.join(file_dir, title)))
                continue

            # 文件不存在，开始下载
            log.info('\t文件不存在开始下载 ... {}'.format(os.path.join(file_dir, title)))
            if len(article_a) > 1:
                time.sleep(3)

                article_click = article_a[1].attrs['onclick']
                split = article_click.split('\'')
                # 获取文章标识
                article_id = split[1]
                article_sg = split[3]
                # print(article_id, article_sg)

                # 获取文章是否支付
                r2 = session.post('http://qikan.cqvip.com/Qikan/Article/GetArticleRight',
                                  data={
                                      'articleId': article_id
                                  },
                                  headers=headers)
                # print(r2.json())

                if r2.json()['RetValue']:
                    log.info('\t文章已支付')
                else:
                    time.sleep(2)
                    log.info('\t文章未支付，开始支付费用')
                    r_pay = session.post('http://qikan.cqvip.com/Qikan/UserPay/BalancePayment',
                                         data={
                                             'id': article_id
                                         },
                                         headers=headers)
                    log.info(r_pay.text)
                    if r_pay.json().get("PromptMsg") != "支付成功":
                        log.info('\t文章支付失败!!!!!!!!!!!!!!!!!!!!!!!!')
                        # 停止运行
                        break

                # 获取文章下载链接
                r3 = session.post('http://qikan.cqvip.com/Qikan/Article/ArticleDown',
                                  data={
                                      'id': article_id,
                                      'info': article_sg,
                                      'ts': int(time.time() * 1000)
                                  },
                                  headers=headers)
                # print(r3.json())

                download_url = r3.json()['url']
                if download_url:
                    log.info('\t下载文章链接 {}'.format(download_url))
                    download(title, author, download_url)
            else:
                log.info('\t文件下载链接获取失败 ... {}'.format(article_a))


def download(title, author, download_url):
    file_name = download_url.split('FileName=')[1]
    if file_name:
        file2write = os.path.join(file_dir, file_name)
        if title in download_list:
            download_exist = download_list[title]
            if file_name.replace(".pdf", "") in download_exist.replace(".pdf", "") or download_exist.replace(".pdf", "") in file_name.replace(".pdf", ""):
                log.info('\t文件已存在类似 ... {} ，原{}'.format(file2write, download_exist))
                with open(file_m, "a", encoding='utf-8') as fm:
                    fm.write("{}|*|{}|*|{}\n".format(title, title + "_" + author, file2write))
                return
        if os.path.exists(file2write):
            log.info('\t文件已存在 ... {}'.format(file2write))
            # 更新目录
            with open(file_m, "a", encoding='utf-8') as fm:
                fm.write("{}|*|{}|*|{}\n".format(title, title+"_"+author, file2write))
        else:
            f = session.get(download_url)
            # 检测编码, 获取header中文文件名
            # file_name_str = str(bytes(f.headers['Content-Disposition'], encoding="iso-8859-1"), encoding="GB2312")
            # fileName = file_name_str.split('filename=')[1]
            # fileName = fileName.replace('"', '').replace("'", "")
            with open(file2write, "wb") as code:
                code.write(f.content)
                # 更新目录
            log.info('\t文件下载完成 ... {}'.format(file2write))
            with open(file_m, "a", encoding='utf-8') as fm:
                fm.write("{}|*|{}|*|{}\n".format(title, title+"_"+author, file2write))


# get_list('U=依托考昔 OR U=安康信')
login()
get_total("U=依托考昔 OR U=安康信  OR U=依托考昔 OR U=安康信 OR U=卡泊芬净 OR U=科赛斯 OR U=氯沙坦 OR U=络沙坦 OR U=洛沙坦 OR U=科素亚 OR U=阿仑膦酸钠 OR U=阿伦磷酸钠 OR U=福善美 OR U=氯沙坦钾氢氯噻嗪 OR U=海捷亚 OR U=厄他培南 OR U=艾他培南 OR U=怡万之 OR U=非那雄胺 OR U=非那司提 OR U=非那甾胺 OR U=保法止 OR U=非那雄胺 OR U=非那司提 OR U=非那甾胺 OR U=保列治 OR U=依那普利 OR U=恩纳普利 OR U=苯酯丙脯酸 OR U=悦宁定 OR U=卡左双多巴 OR U=息宁 OR U=孟鲁司特 OR U=孟鲁斯特 OR U=顺尔宁 OR U=顺耳宁 OR U=亚胺培南 OR U=亚安培南 OR U=泰能 OR U=辛伐他汀 OR U=新伐他汀 OR U=舒降之 OR U=舒降脂 OR U=拉替拉韦 OR U=艾生特 OR U=23价肺炎球菌多糖疫苗 OR U=纽莫法 OR U=甲型肝炎灭活疫苗 OR U=人二倍体甲型肝炎灭活疫苗 OR U=维康特 OR U=西格列汀 OR U=西他列汀 OR U=捷诺维 OR U=西格列汀二甲双胍 OR U=西格列汀二甲双胍 OR U=捷诺达  OR U=依折麦布 OR U=依替米贝 OR U=益适纯 OR U=阿仑膦酸钠维D3 OR U=福美加 OR U=福美佳 OR U=阿瑞匹坦 OR U=阿瑞吡坦 OR U=意美 OR U=地氯雷他定 OR U=恩理思 OR U=糠酸莫米松 OR U=内舒拿 OR U=复方倍他米松 OR U=得宝松 OR U=重组促卵泡素β OR U=普利康 OR U=依折麦布辛伐他汀 OR U=依替米贝辛伐他汀 OR U=葆至能 OR U=重组人干扰素α-2b OR U=甘乐能 OR U=聚乙二醇干扰素α-2b OR U=佩乐能 OR U=替莫唑胺 OR U=泰道 OR U=去氧孕烯炔雌醇 OR U=妈富隆 OR U=去氧孕烯炔雌醇 OR U=美欣乐 OR U=替勃龙 OR U=替勃隆 OR U=利维爱 OR U=十一酸睾酮 OR U=安特尔 OR U=罗库溴铵 OR U=爱可松 OR U=肌松监测仪 OR U=米氮平 OR U=瑞美隆 OR U=依托孕烯 OR U=依伴侬 OR U=泊沙康唑 OR U=诺科飞 OR U=加尼瑞克 OR U=殴加利 OR U=达托霉素 OR U=克必信 OR U=舒更葡糖钠 OR U=布瑞亭 OR U=四价人乳头瘤病毒疫苗 OR U=佳达修 OR U=五价重配轮状病毒减毒活疫苗 OR U=乐儿德 OR U=九价人乳头瘤病毒疫苗 OR U=佳达修 OR U=依巴司韦格佐普韦 OR U=格佐普韦/依巴司韦 OR U=择必达 OR U=依托孕烯炔雌醇阴道环 OR U=舞悠 OR U=帕博利珠单抗 OR U=可瑞")
