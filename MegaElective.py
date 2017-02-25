#coding=utf-8
import os
import sys
import time
import urllib
import urllib2
import cookielib
import json
import random
import re
import pprint
import argparse
import time
import socket
import Image
import cStringIO
import xml.sax
from bs4 import BeautifulSoup as bs
from xml.sax.handler import ContentHandler
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

ISOTIMEFORMAT = "%Y-%m-%d %H:%M:%S"
def get_time():
    return "["+time.strftime(ISOTIMEFORMAT,time.localtime())+"]"
headers = {
            'User-Agent':'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36',
            'Accept':'application/json, text/javascript, */*; q=0.01',
            'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin':'https://iaaa.pku.edu.cn',
            'Referer':'https://iaaa.pku.edu.cn/iaaa/oauth.jsp?appID=syllabus&appName=%E5%AD%A6%E7%94%9F%E9%80%89%E8%AF%BE%E7%B3%BB%E7%BB%9F&redirectUrl=http://elective.pku.edu.cn:80/elective2008/agent4Iaaa.jsp/../ssoLogin.do',
            'X-Requested-With':'XMLHttpRequest'
    }
#jsession=''

pre_url="http://elective.pku.edu.cn/elective2008/edu/pku/stu/elective/controller/supplement/SupplyCancel.do"
refresh_headers = {
        'Host': 'elective.pku.edu.cn',
        'Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36',
        'Accept': '*/*',
        'Referer': pre_url,
        'Accept-Encoding': 'gzip, deflate, sdch',
        'Accept-Language': 'zh-CN,zh;q=0.8'
    }
refresh_postdata=urllib.urlencode({

    })
page_url_prefix="http://elective.pku.edu.cn/elective2008/edu/pku/stu/elective/controller/supplement/supplement.jsp?netui_pagesize=electableListGrid%3B20&netui_row=electableListGrid%3B"
page_headers = {
        'Host': 'elective.pku.edu.cn',
        'Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36',
        'Accept': '*/*',
        'Referer': "",
        'Accept-Encoding': 'gzip, deflate, sdch',
        'Accept-Language': 'zh-CN,zh;q=0.8'
    }
page_postdata=urllib.urlencode({

    })

class MyException(Exception):
    pass


def login(args, cookie, isChange = 0):
    while 1:
        handler = urllib2.HTTPCookieProcessor(cookie)
        opener = urllib2.build_opener(handler)
        #此处的open方法同urllib2的urlopen方法，也可以传入request
        loginUrl='https://iaaa.pku.edu.cn/iaaa/oauthlogin.do'
        postdata=urllib.urlencode({
                'appid': 'syllabus',
                'userName':args.user,
                'password' : args.password,
                'redirUrl' : 'http://elective.pku.edu.cn:80/elective2008/agent4Iaaa.jsp/../ssoLogin.do'
            })
        request=urllib2.Request(loginUrl,postdata,headers)
        response = opener.open(request)
        response=json.loads(response.read().strip())
        if response["success"] != True:
            print(get_time()+u"登陆错误,正在重连，请等待或请检查网络及账号密码")
            time.sleep(args.delay)
        else:
            print(get_time()+u"登陆成功")
            break
    token = response['token']
    #print response
    redir_url="http://elective.pku.edu.cn:80/elective2008/agent4Iaaa.jsp/../ssoLogin.do?rand="+str(random.random())+'&token='+token;
    valid_postdata=urllib.urlencode({
            
        })
    suc=0
    while suc is 0:
        try:
            request=urllib2.Request(redir_url,valid_postdata,headers)
            response = opener.open(request,timeout=4)
            response=response.read().strip()
            suc=1
        except Exception, e:
            pass
        '''
        for item in cookie:
            if item.name is "JSESSIONID":
                item.value = args.sessionid
            elif isChange is 1:
                item.name="FromNewLogin"
                item.value="yes"
        '''
    return cookie


def load_supplycancel(cookie, init = 0):
    refresh_opener=urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie))
    pre_suc=0
    while pre_suc is 0:
        try:
            request=urllib2.Request(pre_url,refresh_postdata,refresh_headers)
            response = refresh_opener.open(request, timeout = 4)
            pre_suc=1
        except urllib2.URLError, e:
            pass
        except socket.timeout, e:
            pass
    response=response.read()
    page_opener=urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie))
    if init is 1:
        global course_list
        course_list = {}
        
        config = open(args.config)
        lines = config.readlines()

        for line_tmp in lines:
            line = line_tmp.split()
            name = line[0].strip().decode("utf-8")
            class_list = []
            for i in xrange(1,len(line)):
                class_list.append(line[i].strip().decode("utf-8"))
            course_list[name]={}
            course_list[name]["name"] = name
            course_list[name]["class_list"] = class_list
            course_list[name]["postfixs"] = []
            course_list[name]["limits"] = []


        for page in xrange(args.pages):
            page_suc=0
            if page != 0:
                page_url = page_url_prefix+str(page*20)
            else:
                page_url = "http://elective.pku.edu.cn/elective2008/edu/pku/stu/elective/controller/supplement/supplement.jsp?netui_pagesize=electableListGrid%3B20"
            while page_suc is 0:
                try:
                    page_headers["Referer"]=page_url
                    request=urllib2.Request(page_url,page_postdata,page_headers)
                    response = page_opener.open(request, timeout = 4)
                    page_suc=1
                except urllib2.URLError, e:
                    pass
                except socket.timeout, e:
                    pass
            response=response.read()
            soup = bs(response.strip(),"html.parser")
            #print(soup.prettify())
            for key,course in course_list.items():
                list = soup.find_all(string=re.compile(course["name"]))
                #print list
#北大壁球馆这种情况
                for item in list:
                    print item
                    if item.find_parent("td").find_previous_siblings() != []:
                        list.remove(item)
#已选上的情况
                is_elected = 0
                for item in list:
                    if item.find_previous(string = re.compile(u"\"已选上列表\"中列出的")) is not None:
                        is_elected = 1
                        course_list.pop(course["name"])
                        break
                    else:
                        
                        class_num = item.find_parent("td").find_next_siblings()[-6].span.string
                        if str(class_num) not in course["class_list"]:
                            continue
                        postfix = item.find_parent("td").find_next_siblings()[-1].a["onclick"]
                        postfix = postfix.split(",")
                        if "confirm" in postfix[0]:
                            index = postfix[-2].strip("\'")
                            seq = postfix[-1].strip("\');")

                        else:
                            index = postfix[-3].strip("\'")
                            seq = postfix[-2].strip("\'")
                        postfix = "?index="+index+"&seq="+seq
                        #print postfix
                        course["postfixs"].append(postfix)
                        limit = item.find_parent("td").find_next_siblings()[-2].span.string
                        limit = int(limit.split("/")[0])
                        course["limits"].append(limit)
                if is_elected == 1:
                    print(course["name"]+u" 已被选上")
                    continue
                elif page == (args.pages-1) :
                    if course["limits"] == []:
                        print(get_time()+course["name"]+u" 没有找到可用的课程，请确认班号")
            '''
            refresh_url="http://elective.pku.edu.cn/elective2008/edu/pku/stu/elective/controller/supplement/refreshLimit.do?"+postfix
            elect_url="http://elective.pku.edu.cn/elective2008/edu/pku/stu/elective/controller/supplement/electSupplement.do?"+postfix
            '''

def get_num(cookie,refresh_url):
    refresh_suc=0
    handler=urllib2.HTTPCookieProcessor(cookie)
    opener = urllib2.build_opener(handler)
    while refresh_suc is 0:
        try:
            request=urllib2.Request(refresh_url,refresh_postdata,refresh_headers)
            response = opener.open(request, timeout = 4)
            refresh_suc=1
        except urllib2.URLError, e:
            pass
        except socket.timeout, e:
            pass
    response = response.read().strip()
    return response


def refresh(cookie):
    #print jsession
    handler=urllib2.HTTPCookieProcessor(cookie)
    opener = urllib2.build_opener(handler)
    '''cookie_str='FromNewLogin=yes;JSESSIONID='+jsession;'''
    load_supplycancel(cookie, init = 0)

    while course_list != {}:
        start_over = 0
        for key, course in course_list.items():
            now = -2
            print(get_time()+u"检查课程： "+course["name"])
            cnt = -1
            for postfix in course["postfixs"]:
                cnt = cnt + 1
                response = get_num(cookie,"http://elective.pku.edu.cn/elective2008/edu/pku/stu/elective/controller/supplement/refreshLimit.do"+postfix)
                #print postfix
                handler = ContentHandler()
                #print response
                try:
                    root=ET.fromstring(response)
                    if root[0].text is not None:
                        now=int(root[0].text)
                except Exception, e:
                    pass
                if int(now) == -1:
                    print(get_time()+course["name"]+u" 获取名额失败")
                if now == course['limits'][cnt]:
                    print(get_time()+course["name"]+" "+str(course["limits"][cnt])+"/"+str(now))
                if now < course['limits'][cnt]:
                    if now < 0:
                        continue
                    else:
                        print(get_time()+course["name"]+u" 发现名额"+" "+str(course["limits"][cnt])+"/"+str(now))
                        elect(cookie,postfix,course['name'])
                        load_supplycancel(cookie,init=1)
                        start_over = 1
                        break
                time.sleep(args.delay)
            if start_over is 1:
                break;


def check_elected(response,name):
    soup = bs(response,"html.parser")
    head = soup.find(string = re.compile(u"\"已选上列表\"中列出的"))
    try:
        if head.find_next(string = re.compile(name)) != None:
            print(get_time()+u"已选上 "+name)
        else:
            f = open('error.log','wb')
            f.write(response)
            f.close()
            print(get_time()+u"未选上 "+name)
    except Exception, e:
        f = open('error.log','wb')
        f.write(response)
        f.close()
        print(get_time()+u"未选上 "+name)

def elect(cookie,postfix,name):
    elect_url = "http://elective.pku.edu.cn/elective2008/edu/pku/stu/elective/controller/supplement/electSupplement.do"+postfix
    print(get_time()+u"开始选择 "+name)
    load_supplycancel(cookie,init=0)

    elect_headers = {
		#Cookie:FromNewLogin=yes; JSESSIONID=Q3x3WLnZHcbbZzTBJ9pnJYq0w7BGL0F6JJjTpvvDGZSCgTttp29w!-818398110!105135227,
		'Host':'elective.pku.edu.cn',
                'Referer':"http://elective.pku.edu.cn/elective2008/edu/pku/stu/elective/controller/supplement/electSupplement.do"+postfix,
		'User-Agent':'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36'
        }

    elect_opener=urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie))
    elect_postdata=urllib.urlencode({
            
        })

    request=urllib2.Request(elect_url, elect_postdata, elect_headers)
    response = elect_opener.open(request)
    response = response.read().strip()
    #print response
    check_elected(response,name)


def valid(cookie):
    valid_headers = {
    	'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
		'Accept-Encoding':'gzip, deflate, sdch',
		'Accept-Language':'zh-CN,zh;q=0.8',
		'Connection':'keep-alive',
		#Cookie:FromNewLogin=yes; JSESSIONID=Q3x3WLnZHcbbZzTBJ9pnJYq0w7BGL0F6JJjTpvvDGZSCgTttp29w!-818398110!105135227,
		'Host':'elective.pku.edu.cn',
		'Upgrade-Insecure-Requests':'1',
		'User-Agent':'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36'
        }
    
    valid_opener=urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie))
    valid_postdata=urllib.urlencode({
            
        })
    valid_url = "http://elective.pku.edu.cn/elective2008/DrawServlet?Rand=1000"
    request=urllib2.Request(valid_url,valid_postdata,valid_headers)
    response = valid_opener.open(request)
    response = response.read()
    file = cStringIO.StringIO(response)
    img = Image.open(file)
    img.show()
    print("请输入验证码：")
    code = raw_input()
    send_url = "http://elective.pku.edu.cn/elective2008/edu/pku/stu/elective/controller/supplement/validate.do?validCode=" + code
    send_headers = {
            'Accept': "*/*",
                    'Accept-Encoding':'gzip, deflate, sdch',
                    'Accept-Language':'zh-CN,zh;q=0.8',
                    'Connection':'keep-alive',
                    #Cookie:FromNewLogin=yes; JSESSIONID=Q3x3WLnZHcbbZzTBJ9pnJYq0w7BGL0F6JJjTpvvDGZSCgTttp29w!-818398110!105135227,
                    'Host':'elective.pku.edu.cn',
                    'Referer':"http://elective.pku.edu.cn/elective2008/edu/pku/stu/elective/controller/supplement/SupplyCancel.do",
                    'Upgrade-Insecure-Requests':'1',
                    'User-Agent':'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36'
            }
    send_opener=urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie))
    send_postdata=urllib.urlencode({
            
        })
    request=urllib2.Request(send_url,send_postdata,send_headers)
    response = send_opener.open(request)
    response = response.read()
    #print response
    return bs(response,"lxml").valid.string


def main(args_parser):
    global args
    args = args_parser
    cookie = cookielib.CookieJar()
    global delay
    delay = args.delay
    vcookie = login(args,cookie)
    load_supplycancel(vcookie,init = 1)
    if course_list == {}:
        print(u"无候选课程")
    else:
        print(get_time()+u"载入课程成功")
        print(u"候选课程： ")
        for key, course in course_list.items():
            print(course["name"])
        result = 0
        while 1:
            result = int(valid(vcookie))
            if result != 2:
                print(u"验证码不正确，请重新验证")
                time.sleep(args.delay)
            else:
                print(get_time()+u"验证成功")
                break

        refresh(vcookie)
        print(get_time()+u"所有课程选择结束")

#   for item in cookie:
#       print item.name
#       print item.value

#   why I need pre-load?f$#%
    '''
    pre_url="http://elective.pku.edu.cn/elective2008/edu/pku/stu/elective/controller/supplement/SupplyCancel.do"
    pre_suc=0
    refresh_headers = { 
             'Host': 'elective.pku.edu.cn',
                'Connection': 'keep-alive',
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36',
                'Accept': '*/*',
                'Referer': 'http://elective.pku.edu.cn/elective2008/edu/pku/stu/elective/controller/supplement/SupplyCancel.do',
                'Accept-Encoding': 'gzip, deflate, sdch',
                'Accept-Language': 'zh-CN,zh;q=0.8'
           
            } 
    refresh_opener=urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie))
    refresh_postdata=urllib.urlencode({  
        })
    while pre_suc is 0:
        try:
            request=urllib2.Request(pre_url,refresh_postdata,refresh_headers)
            response = refresh_opener.open(request, timeout = 4)
            pre_suc=1
            
        except urllib2.URLError, e:
            pass
    '''

def parse_arguments(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('--user', type = str)
    parser.add_argument('--password', type = str)
    parser.add_argument('--pages', type = int)
    parser.add_argument('--config', type = str, default = "./config")
    parser.add_argument('--delay', type = float, default = 3.5)
    return parser.parse_args(argv)


if __name__ == '__main__':
    main(parse_arguments(sys.argv[1:]))
