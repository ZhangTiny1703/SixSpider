# coding=gbk

import requests
from bs4 import BeautifulSoup
import time
import os
import sys
import http.cookiejar as HC
import random
import traceback
import urllib
from urllib import parse
from numpy import random
import re
import json
import logging
from logging.handlers import TimedRotatingFileHandler
import socket
import EasySqlite

socket.setdefaulttimeout(20)
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
log_file_handler = TimedRotatingFileHandler(filename=os.path.join(base_path, r"article/cnki_run.log"), when="D",
                                            interval=1, backupCount=7, encoding='utf-8')
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
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'
    , 'Accept-Encoding': 'gzip, deflate'
    , 'Accept-Language': 'zh-CN,zh;q=0.9'
    , 'Cache-Control': 'max-age=0'
    , 'Connection': 'keep-alive'
    , 'Host': 'kns.cnki.net'
    , 'Upgrade-Insecure-Requests': '1'
    ,
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'
}

# 20s过期时间
global_timeout = 20
# 登陆信息
data = {
    'userName': 'sherry.huang@goal-noah.com',
    'pwd': '33530912'
}

# 下载文件存储目录
# file_dir = os.path.join(base_path, "中国知网")
cur_day = time.strftime('%Y-%m-%d', time.localtime(time.time()))
if cur_day > '2099-03-01':
    log.info("授权已过期")
    exit()

file_dir = os.path.join(base_path, "中国知网", cur_day)
if os.path.exists(file_dir):
    print("目录{}已存在，下载文件中...".format(file_dir))
else:
    print("目录{}不存在，创建该目录...".format(file_dir))
    os.mkdir(file_dir)

# 连接目录表Sqlite
db = EasySqlite.EasySqlite(os.path.join(base_path, r"article/article.db"))

# 请求的全局session
session = requests.Session()

cookie_path = os.path.join(base_path, r"article\qikan-cnki-cookie.txt")

session.cookies = HC.MozillaCookieJar(filename=cookie_path)

session.get('https://www.cnki.net/', headers=headers, allow_redirects=False)
session.get('https://kns.cnki.net/kns/brief/result.aspx?dbprefix=CJFQ&crossDbcodes=CJFQ,CDFD,CMFD,CPFD,IPFD,CCND,CCJD',
            headers=headers)
session.get('https://kns.cnki.net/kns/brief/result.aspx', headers=headers)


def login():
    # 多步登陆获取完整cookie
    session.get('https://login.cnki.net/TopLogin/api/loginapi/Logout', headers=headers)
    session.get(
        'https://kns.cnki.net/kns/brief/result.aspx?dbprefix=CJFQ&crossDbcodes=CJFQ,CDFD,CMFD,CPFD,IPFD,CCND,CCJD',
        headers=headers)
    # cookie新增SID_klogin
    session.get('https://kns.cnki.net/KLogin/Request/GetKFooter.ashx', headers=headers)
    r = session.get('https://login.cnki.net/TopLogin/api/loginapi/Login?isAutoLogin=false&'
                    + urllib.parse.urlencode(data) + '&_=' + str(int(time.time() * 1000)))
    user_info = json.loads(r.text[1: -1])
    if user_info.get('IsSuccess'):
        log.info('登陆成功 ... ' + json.dumps(user_info))
        login_header = {
            'Host': 'login.cnki.net',
            'Pragma': 'no-cache',
            'Referer': 'https://kns.cnki.net/kns/brief/result.aspx?dbprefix=CJFQ&crossDbcodes=CJFQ,CDFD,CMFD,CPFD,IPFD,CCND,CCJD'
        }
        session.post('https://kns.cnki.net/kns/Loginid.aspx', data={'uid': user_info.get('Uid')},
                     headers={**headers, **login_header})
        session.cookies.save()
    else:
        log.error('登陆失败 ... ' + json.dumps(user_info))
        exit('登陆失败 ... ')

    try:
        session.cookies.load(ignore_discard=True, ignore_expires=True)
        cookie_str = ""
        for cookie in session.cookies:
            # print(cookie.name, cookie.value)
            cookie_str = cookie_str + cookie.name + "=" + cookie.value + ";"
        cookie_str = cookie_str + 'cnkiUserKey=09335600-3228-c095-c5cd-b1459792ec88'
        # print(cookie_str)
        headers['Cookie'] = cookie_str

    except Exception as e:
        log.error('未找到cookies文件')
        log.error(traceback.format_exc())


def get_total(key):
    headers[
        'Referer'] = 'Referer: https://kns.cnki.net/kns/brief/result.aspx?dbprefix=CJFQ&crossDbcodes=CJFQ,CDFD,CMFD,CPFD,IPFD,CCND,CCJD'

    s_handle_data = {
        'action': ''
        , 'NaviCode': 'E'
        , 'ua': '1.21'
        , 'isinEn': '1'
        , 'PageName': 'ASP.brief_result_aspx'
        , 'DbPrefix': 'CJFQ'
        , 'DbCatalog': '中国学术期刊网络出版总库'
        , 'ConfigFile': 'CJFQ.xml'
        , 'db_opt': 'CJFQ'
        , 'expertvalue': key
        , 'his': '0'
        , 'year_from': '2020'
        , 'year_to': '2020'
        , 'year_type': 'echar'
        , 'his': '0'
        , 'db_cjfqview': '中国学术期刊网络出版总库,WWJD'
        , 'db_cflqview': '中国学术期刊网络出版总库'
        , '__': 'Thu Jan 10 2020 15:05:25 GMT+0800 (中国标准时间)'
    }
    # 设置查询条件，请求一次
    total_url = 'https://kns.cnki.net/kns/request/SearchHandler.ashx'
    r_param = session.post(total_url, data=s_handle_data, headers=headers)
    param_dict = dict(parse.parse_qsl("pagename=" + r_param.text))

    # 获取查询列表
    r_list_doc = session.get(
        'https://kns.cnki.net/kns/brief/brief.aspx?pagename=' + r_param.text + '&t='
        + str(int(time.time() * 1000)) + '&keyValue=&S=1&sorttype=(FFD%2c%27RANK%27)+desc',
        headers=headers)
    r_list_doc.encoding = 'utf-8'
    # print(r_list_doc.text)

    soup = BeautifulSoup(r_list_doc.text, 'lxml', from_encoding='utf-8')
    result = soup.select('#resultcount')
    result_count = int(result[0].attrs['value'])
    page_size = 50
    page_count = int((result_count + page_size - 1) / page_size)
    log.info("找到 {} 条结果，共分 {} 页".format(result_count, page_count))

    # 开始分页下载
    for page_num in range(1, page_count+1):
        get_list(key, page_size, page_num, param_dict)
        time.sleep(10)
        if page_num * page_size >= 6000:
            log.info("总记录数已达6000，停止翻页......")
            break
    log.info(">>>>>>>>>>当前关键词执行完成 .................")


def get_list(key, page_size, page_num, param_dict):
    page_data = {
        'curpage': page_num
        , 'RecordsPerPage': page_size
        , 'QueryID': random.random_integers(1, 9)
        , 'ID': ''
        , 'turnpage': page_num - 1 if page_num - 1 > 0 else page_num + 1
        , 'tpagemode': 'L'
        , 'Fields': ''
        , 'DisplayMode': 'listmode'
        , 'dbPrefix': param_dict['dbPrefix']
        , 'PageName': param_dict['pagename']
        , 'sorttype': "(FFD,'RANK') desc"
        , 'isinEn': param_dict['isinEn']
    }
    # 获取查询列表
    list_url = 'https://kns.cnki.net/kns/brief/brief.aspx?' + urllib.parse.urlencode(page_data)
    r_list_doc = session.get(list_url, headers=headers, timeout=global_timeout)
    r_list_doc.encoding = 'utf-8'
    log.info(list_url)

    soup = BeautifulSoup(r_list_doc.text, 'lxml', from_encoding='utf-8')
    headers['Referer'] = list_url
    trs = soup.select('.GridTableContent tr')
    # 去除标题栏
    for tr in trs[1:]:
        tds = tr.select('td')
        # 序号
        tr_order = tds[0].text

        # 标题名
        tr_title = tds[1].select('a')[0].text
        tr_title = tr_title.replace("'", "-")

        # 作者
        tr_authors = ""
        authors_a = tds[2].select('a')
        for author_a in authors_a:
            tr_authors = tr_authors + "_" + author_a.text
        # 首作
        tr_author = ""
        if len(authors_a) > 0:
            tr_author = authors_a[0].text
            tr_author = tr_author.replace("'","-")

        # 刊名
        from_source = ""
        if len(tds) > 3:
            if len(tds[3].select('a')) > 0:
                from_source = tds[3].select('a')[0].text

        # 发表时间
        tr_time = ""
        if len(tds) > 4:
            tr_time = tds[4].text

        # 被引
        tr_db = ""
        if len(tds) > 5:
            tr_db = tds[5].text

        # 下载 https://kns.cnki.net/kns/download.aspx
        tr_down_url = ""
        if len(tds) > 6:
            if len(tds[6].select('a')) > 0:
                tr_down_url = tds[6].select('a')[0].attrs['href']

        # 阅读
        type = ""
        if len(tds) > 7:
            if len(tds[7].select('a')) > 0:
                type = tds[7].select('a')[0].attrs['title']
        if type == "HTML阅读":
            tr_file_type = ".pdf"
        elif type == "阅读":
            tr_file_type = ".caj"
        else:
            tr_file_type = ""
            log.info("文件类型未知，原文类型{}".format(type))

        # 输出表格列表
        log.info(
            "{},{},{},{},{},{}".format(tr_order, tr_title, tr_author, tr_file_type, tr_time.strip(), tr_db.strip()))
        # 文件重复去重
        file_will_write = os.path.join(file_dir, tr_title)

        if check_before_download(tr_title, tr_author, from_source):
            log.info('\t文件不存在，开始下载 ... {}'.format(file_will_write))

            article_url = 'https://kns.cnki.net' + tds[1].select('a')[0].attrs['href']
            article_response = session.get(article_url, headers=headers, timeout=global_timeout)
            article_soup = BeautifulSoup(article_response.text, 'lxml', from_encoding='utf-8')
            pdf_down = article_soup.select_one("#pdfDown")
            # 有pdf下载按钮才会触发
            if pdf_down:
                download_url = pdf_down.attrs['href']
                if not str(download_url).startswith("http"):
                    download_url = 'https://kns.cnki.net' + download_url
                if str(download_url).startswith("https://chkdx.cnki.net"):
                    log.info('\tpdf下载链接无权限 ... 文章链接{}'.format(download_url))
                else:
                    log.info('\t下载链接 ... {}'.format(download_url))
                    download(tr_title, tr_author, download_url)
                    time.sleep(6)
            else:
                log.info('\t无pdf下载链接 ... 文章链接{}'.format(article_url))


def download(title, author, down_url):
    # print(down_url)
    down_headers = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Encoding': 'gzip, deflate',
                    'Accept-Language': 'zh-CN,zh;q=0.9',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'
                    }
    down_cookie_str = ""
    for cookie in session.cookies:
        down_cookie_str = down_cookie_str + cookie.name + "=" + cookie.value + ";"
    # down_headers['Cookie'] = 'Ecp_ClientId=6190110100400259207; Ecp_IpLoginFail=190110180.154.19.189; cnkiUserKey=4b9d957f-13fe-14e8-d403-3e23572f9704; Ecp_lout=1; LID=WEEvREcwSlJHSldTTEYzVDhsN3d3MVE5VHVvSUlqLzBCZEQrbUdPS0dIaz0=$9A4hF_YAuvQ5obgVAqNKPCYcEjKensW4IQMovwHtwkF4VYPoHbKxJw!!; Ecp_session=1; ASP.NET_SessionId=mxjqbr3lvwl3xccwtevicvwd; SID_kns=011115; SID=011101; KNS_SortType=; RsPerPage=20; _pk_ref=%5B%22%22%2C%22%22%2C1547198945%2C%22http%3A%2F%2Fwww.cnki.net%2F%22%5D; _pk_ses=*'
    down_headers['Cookie'] = down_cookie_str[:-1]
    # print_cookie()

    # 第一次请求重定向
    down_headers['Host'] = get_host(down_url)['host']
    # r_d = session.get(down_url, headers=down_headers, allow_redirects=False)
    r_d = session.get(down_url, headers=down_headers, allow_redirects=False, timeout=global_timeout)
    loc_pubdownload = r_d.headers.get('Location', None)
    print(r_d.headers)

    # 第二次请求重定向
    down_headers['Host'] = get_host(r_d.headers.get('Location'))['host']
    r_d = session.get(loc_pubdownload, headers=down_headers, allow_redirects=False, timeout=global_timeout)
    loc_pubdownload = r_d.headers.get('Location', None)
    print(r_d.headers)

    # 这一步验证是否已支付，如果未支付，该步骤则返回的是页面，没有location
    if loc_pubdownload:
        # print(session.cookies)
        # 第三次请求，pubdownload，如果未支付，则返回页面，如果已支付，则继续重定向直到下载
        down_headers['Host'] = get_host(loc_pubdownload)['host']
        r_pubdownload = session.get(loc_pubdownload, headers=down_headers, allow_redirects=False, timeout=global_timeout)
        r_pubdownload.encoding = 'utf-8'
        print(r_pubdownload.headers)
        # print(r_pubdownload.status_code)
        # print(r_pubdownload.text)

        if r_pubdownload.status_code == 200:
            # 返回的是页面
            log.info('\t文章未支付，支付中 ...')
            time.sleep(2)
            pay_data = {
                'pid': 'cjfq',
                'uid': requests.utils.dict_from_cookiejar(session.cookies).get('LID')
            }
            # session.close()
            down_headers['Host'] = get_host(loc_pubdownload)['host']
            r_pay = session.post(loc_pubdownload, data=pay_data, headers=down_headers, allow_redirects=False, timeout=global_timeout)
            r_pay.encoding = 'utf-8'
            print(loc_pubdownload)
            print(r_pay.headers)
            if r_pay.status_code == 302:
                log.info('\t文章支付完成 ...{}'.format(r_pay.headers))
                time.sleep(2)
                # 返回的是文件流
                # 循环直到r = 200, 重定向到最后的下载链接，
                r = r_pay
                try:
                    while r.status_code == 302:
                        r_location = r.headers.get('Location')
                        if str(r_location).startswith("http"):
                            down_headers['Host'] = get_host(r.headers.get('Location'))['host']
                        else:
                            r_location = "https://" + down_headers['Host'] + "/cjfdsearch/" + r_location
                        session.close()
                        r = session.get(r_location, headers=down_headers, allow_redirects=False, timeout=global_timeout)
                        print(r_location)
                except:
                    log.error(traceback.format_exc())
                    log.error(r.headers)
                    exit()

                # 保存文件
                save_file(title, author, r)
            else:
                log.error('\t文章支付无效 ...{}'.format(r_pay.headers))
                log.error('\t文章链接 ...{}'.format(down_url[0:]))

        else:
            # 返回的是文件流
            log.info('\t文章不需要支付，直接下载 ...')
            # 循环直到r = 200, 重定向到最后的下载链接
            r = r_pubdownload
            try:
                while r.status_code == 302:
                    r_location = r.headers.get('Location')
                    if str(r_location).startswith("http"):
                        down_headers['Host'] = get_host(r.headers.get('Location'))['host']
                    else:
                        r_location = "https://" + down_headers['Host'] + "/cjfdsearch/" + r_location
                    r = session.get(r_location, headers=down_headers, allow_redirects=False, timeout=global_timeout)
            except:
                log.error(traceback.format_exc())
                log.error(r.headers)
                exit()

            # 保存文件
            save_file(title, author, r)
    else:
        log.error('\t下载文章连接无效，{}'.format(loc_pubdownload))


# 获取请求url域名
def get_host(url):
    pattern = re.compile(r'(.*?)://(.*?)/', re.S)
    response = re.search(pattern, str(url))
    if response:
        return {'header': str(response.group(1)).strip(), 'host': str(response.group(2)).strip()}
    else:
        return None


def save_file(title, author, response):
    orginal_file_name = response.headers.get('Content-Disposition')
    if orginal_file_name:
        # 检测编码, 获取header中文文件名
        try:
            file_name_str = str(bytes(orginal_file_name, encoding="iso-8859-1"), encoding="GBK")
        except :
            file_name_str = str(bytes(orginal_file_name, encoding="iso-8859-1"), encoding="utf-8")
        file_name = file_name_str.split('filename=')[1]
        file_name = file_name.replace('"', '')
        file_name = urllib.parse.unquote(file_name, encoding='utf-8', errors='replace')
        # print(file_name)

        file2write = os.path.join(file_dir, file_name)
        if not check_when_download(file_name, file2write, title, author):
            return
        if os.path.exists(file2write):
            log.info('\t文件已存在 ... {}'.format(file2write))
            insert_db(title, author, file_name.replace(".pdf", ""), file2write)
        else:
            # 下载内容
            with open(file2write, "wb") as code:
                code.write(response.content)

            if os.path.getsize(file2write) > 0:
                log.info('\t文件下载完成 ... {}'.format(file2write))
                insert_db(title, author, file_name.replace(".pdf", ""), file2write)
            else:
                os.remove(file2write)
                log.info('\t文件下载不完整,已删除 ... {}'.format(file2write))
    else:
        log.error('\t文件无法下载 ... {}'.format(response.headers))
        log.error(response.text)

    # 下载完成后关闭
    response.close()
    time.sleep(2)


def check_before_download(tr_title, tr_author, from_source):
    if_down = True
    # 去掉包含关键字的题目
    key_ignore = ["总目次", "索引", "总目录", "鼠"]
    for key_i in key_ignore:
        if key_i in tr_title:
            log.info('\t当前文章标题包含关键字 {} ，已忽略下载'.format(key_i))
            if_down = False
            break

    # 来源关键词过滤
    rows_source = db.execute(
        "select * from article_exclude where source='中国知网' and (article_result='{}' or article_source='{}')".format(
            from_source, from_source))
    if len(rows_source) > 0:
        log.info('\t文件来源存在于过滤条件 ... 来源 {}'.format(from_source))
        if_down = False

    # 相同网站文件重复去重-标题名加作者
    rows_title_author = db.execute(
        "select * from article_down where source='中国知网' and title='{}' and head_author='{}'".format(
            tr_title, tr_author))
    if len(rows_title_author) > 0:
        log.info('\t文件已存在当前网站目录列表 ... {}'.format(os.path.join(file_dir, tr_title)))
        if_down = False

    # 不同网站重复去重-根据标题
    rows_title = db.execute(
        "select * from article_down where source='维普网' and title='{}'".format(
            tr_title))
    if len(rows_title) > 0:
        log.info('\t文件已存在其他网站目录列表 ... {}'.format(os.path.join(file_dir, tr_title)))
        if_down = False
    return if_down


def check_when_download(file_name, file2write, title, author):
    if_down = True
    rows = db.execute("select * from article_down where source='中国知网' and title='{}'".format(title))
    if len(rows) > 0:
        for row in rows:
            download_exist = row.get("file_name")
            if file_name.replace(".pdf", "") in download_exist or download_exist in file_name.replace(".pdf", ""):
                log.info('\t文件已存在类似 ... {} ，原{}'.format(file2write, download_exist))
                insert_db(title, author, file_name.replace(".pdf", ""), file2write)
                if_down = False
                break
    return if_down


def insert_db(title, head_author, file_name, path):
    db.execute("insert into article_down(source,type,title,head_author,file_name,path) "
               "values ('中国知网','期刊','{}','{}','{}','{}')".format(title, head_author, file_name, path))


def print_cookie():
    for cookie in session.cookies:
        log.info(cookie.name, cookie.value)


login()
log.info("》》》》》》》》》查询第一组关键词》》》》》》》》》")
get_total(
    "FT=依托考昔 OR FT=安康信 OR FT=卡泊芬净 OR FT=科赛斯 OR FT=氯沙坦 OR FT=络沙坦 OR FT=洛沙坦 OR FT=科素亚 OR FT=阿仑膦酸钠 OR FT=阿伦磷酸钠 OR FT=福善美 OR FT=氯沙坦钾氢氯噻嗪 OR FT=海捷亚 OR FT=厄他培南 OR FT=艾他培南 OR FT=怡万之 OR FT=非那雄胺 OR FT=非那司提 OR FT=非那甾胺 OR FT=保法止 OR FT=非那雄胺 OR FT=非那司提 OR FT=非那甾胺 OR FT=保列治 OR FT=依那普利 OR FT=恩纳普利 OR FT=苯酯丙脯酸 OR FT=悦宁定 OR FT=卡左双多巴 OR FT=息宁 OR FT=孟鲁司特 OR FT=孟鲁斯特 OR FT=顺尔宁 OR FT=顺耳宁 OR FT=亚胺培南 OR FT=亚安培南 OR FT=泰能 OR FT=辛伐他汀 OR FT=新伐他汀 OR FT=舒降之 OR FT=舒降脂 OR FT=拉替拉韦 OR FT=艾生特 OR FT=23价肺炎球菌多糖疫苗 OR FT=纽莫法 OR FT=甲型肝炎灭活疫苗(人二倍体细胞) OR FT=人二倍体甲型肝炎灭活疫苗 OR FT=维康特 OR FT=西格列汀 OR FT=西他列汀 OR FT=捷诺维 OR FT=西格列汀二甲双胍 OR FT=西格列汀二甲双胍 OR FT=捷诺达 OR FT=依折麦布 OR FT=依替米贝 OR FT=益适纯 OR FT=阿仑膦酸钠维D3 OR FT=福美加 OR FT=福美佳 OR FT=阿瑞匹坦 NOT KY=meta")

log.info("》》》》》》》》》休息5秒，查询第二组关键词》》》》》》》》》")
time.sleep(5)
get_total(
    "FT=地氯雷他定 OR FT=恩理思 OR FT=糠酸莫米松 OR FT=内舒拿 OR FT=复方倍他米松 OR FT=得宝松 OR FT=重组促卵泡素β OR FT=普利康 OR FT=依折麦布辛伐他汀 OR FT=依替米贝辛伐他汀 OR FT=葆至能 OR FT=替莫唑胺 OR FT=泰道 OR FT=去氧孕烯炔雌醇 OR FT=妈富隆 OR FT=去氧孕烯炔雌醇 OR FT=美欣乐 OR FT=替勃龙 OR FT=替勃隆 OR FT=利维爱 OR FT=十一酸睾酮 OR FT=安特尔 OR FT=罗库溴铵 OR FT=爱可松 OR FT=肌松监测仪 OR FT=米氮平 OR FT=瑞美隆 OR FT=依托孕烯 OR FT=依伴侬 OR FT=泊沙康唑 OR FT=诺科飞 OR FT=加尼瑞克 OR FT=殴加利 OR FT=达托霉素 OR FT=克必信 OR FT=舒更葡糖钠 OR FT=布瑞亭 OR FT=四价人乳头瘤病毒疫苗 OR FT=佳达修 OR FT=五价重配轮状病毒减毒活疫苗 OR FT=乐儿德 OR FT=九价人乳头瘤病毒疫苗 OR FT=佳达修 OR FT=依巴司韦格佐普韦 OR FT=择必达 OR FT=依托孕烯炔雌醇阴道环 OR FT=舞悠 OR FT=帕博利珠单抗 OR FT=可瑞达 OR FT=阿瑞吡坦 OR FT=意美 OR FT=特地唑胺 OR FT=赛威乐 NOT KY=meta")

log.info(">>>>>>>>>>程序执行完成 .................")
# log.info("》》》》》》》》》休息2秒，继续查询第二组关键词》》》》》》》》》")
# time.sleep(2)
# get_total(
#     "FT=舒降之 OR FT=舒降脂 OR FT=拉替拉韦 OR FT=艾生特 OR FT=23价肺炎球菌多糖疫苗 OR FT=纽莫法 OR FT=甲型肝炎灭活疫苗(人二倍体细胞) OR FT=人二倍体甲型肝炎灭活疫苗 OR FT=维康特 OR FT=西格列汀 OR FT=西他列汀 OR FT=捷诺维 OR FT=西格列汀二甲双胍 OR FT=西格列汀二甲双胍 OR FT=捷诺达 OR FT=依折麦布 OR FT=依替米贝 OR FT=益适纯 OR FT=阿仑膦酸钠维D3 OR FT=福美加 OR FT=福美佳 OR FT=阿瑞匹坦 OR FT=阿瑞吡坦 OR FT=意美 OR FT=地氯雷他定 OR FT=恩理思 OR FT=糠酸莫米松 OR FT=内舒拿 OR FT=复方倍他米松 OR FT=得宝松 OR FT=重组促卵泡素β OR FT=普利康 OR FT=依折麦布辛伐他汀 OR FT=依替米贝辛伐他汀 OR FT=葆至能 OR FT=重组人干扰素α-2b")
#
# log.info("》》》》》》》》》休息2秒，继续查询第三组关键词》》》》》》》》》")
# time.sleep(2)
# get_total(
#     "FT=甘乐能 OR FT=聚乙二醇干扰素α-2b OR FT=佩乐能 OR FT=替莫唑胺 OR FT=泰道 OR FT=去氧孕烯炔雌醇 OR FT=妈富隆 OR FT=去氧孕烯炔雌醇 OR FT=美欣乐 OR FT=替勃龙 OR FT=替勃隆 OR FT=利维爱 OR FT=十一酸睾酮 OR FT=安特尔 OR FT=罗库溴铵 OR FT=爱可松 OR FT=肌松监测仪 OR FT=米氮平 OR FT=瑞美隆 OR FT=依托孕烯 OR FT=依伴侬 OR FT=泊沙康唑 OR FT=诺科飞 OR FT=加尼瑞克 OR FT=殴加利 OR FT=达托霉素 OR FT=克必信 OR FT=舒更葡糖钠 OR FT=布瑞亭 OR FT=四价人乳头瘤病毒疫苗 OR FT=佳达修 OR FT=五价重配轮状病毒减毒活疫苗 OR FT=乐儿德 OR FT=九价人乳头瘤病毒疫苗 OR FT=佳达修 OR FT=依巴司韦格佐普韦 OR FT=格佐普韦 OR FT=依巴司韦 OR FT=择必达 OR FT=依托孕烯炔雌醇阴道环 OR FT=舞悠 OR FT=帕博利珠单抗 OR FT=可瑞达")

# download("基于江南原生态理念的水居民宿设计——以原舍·阅水民宿设计为例.pdf",
#          "https://kns.cnki.net/kns/download.aspx?filename=s9Ge4EVaSNXewMFT3p2Z2RjdSBnW5Q2L5cVS4p2UIZTb6Flcp92dnJGepBTSGZUZthWQWpXYkFVY5x2QzoWWjZ2ZEF3QSNlduRjS6NlZXdkMmhDWFB1Y4kma0MmUGhGd4MUMnFXNnB1an9maxMGMVN3ZIljbqdUT&tablename=CJFDPREP")
# download("辛伐他汀片体外溶出一致性评价方法的建立_郭志渊_谢华_袁军.pdf",
#          "https://kns.cnki.net/kns/download.aspx?filename=OhkdJJUYJRlbPdWWEJHb4ATNT1WR2RnUyhmMvVnSUFkMx1mNWV1TpJGRwIkaSp1YaJWbnZkQFFWevJnar8iN6xmW3cTcQN3Mj9SS5YEOrgTNjF3T3dTc5oUVq1WaFpkSy8mci9GNlJTavxkWRhmQxlFVOFUTLJUN&tablename=CAPJDAY")

# removeHandler 要放在程序运用打印日志的后面
log.removeHandler(log_file_handler)
if os.path.exists(cookie_path):
    os.remove(cookie_path)
