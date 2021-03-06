# -*- coding: utf-8 -*-
# author: HuYong, MikeHuang

from bs4 import BeautifulSoup
from urllib import quote


# 从网页中解析完整跳转链接
def getSelectUrl(response, text):
    html = response.content.decode("gb2312")
    soup = BeautifulSoup(html.decode("utf-8"), "html5lib")
    links = soup.select('ul a')
    selectUrl = [link for link in links if link.string == text][0]['href']
    paramlist = selectUrl.split('&')
    unicodename = paramlist[1][3:]
    urlname = quote(unicodename.encode())
    paramlist[1] = 'xm=' + urlname
    return '&'.join(paramlist)



# 从网页中解析学生信息
def getStudentInfor(response):
    html = response.content.decode("gb2312")
    soup = BeautifulSoup(html.decode("utf-8"), "html5lib")
    d = {}
    d["studentnumber"] = soup.find(id="xh")
    d["idCardNumber"] = soup.find(id="lbl_sfzh")
    d["name"] = soup.find(id="xm")
    d["sex"] = soup.find(id="lbl_xb")
    d["enterSchoolTime"] = soup.find(id="lbl_rxrq")
    d["birthsday"] = soup.find(id="lbl_csrq")
    d["highschool"] = soup.find(id="lbl_byzx")
    d["nationality"] = soup.find(id="lbl_mz")
    d["hometown"] = soup.find(id="lbl_jg")
    d["politicsStatus"] = soup.find(id="lbl_zzmm")
    d["college"] = soup.find(id="lbl_xy")
    d["major"] = soup.find(id="lbl_zymc")
    d["classname"] = soup.find(id="lbl_xzb")
    d["gradeClass"] = soup.find(id="lbl_dqszj")
    for k,v in d.items():
        if v != None:
            d[k] = v.string
    return d


# 从网页中解析课表信息
def getClassScheduleFromHtml(response):
    html = response.content.decode("gb2312","ignore")
    soup = BeautifulSoup(html.decode("utf-8"), "html5lib")
    __VIEWSTATE = soup.findAll(name="input")[2]["value"]
    table = soup.select("table")
    if table:
        trs = soup.find(id="DBGrid").find_all('tr')[1:]
    else:
        return None
    oneClassKeys = ["selectClassCode","classNo","name", "Compulsory", "type", \
                    "teacher","point", "totalTimeInWeek", "time",  "location"]
    classes = []
    for tr in trs:
        tds = tr.find_all('td')
        oneClassValues = []
        for td in tds:
            #if td.string == None:
            for child in td.children:
                if not unicode(child.string).startswith("\n"):
                    if unicode(child.string) != u'\xa0':
                        oneClassValues.append(child.string)
                    else:
                        oneClassValues.append(None)
        while len(oneClassValues) < len(oneClassKeys):
            oneClassValues.append("")

        oneClass = dict((key, value) for key, value in zip(oneClassKeys, oneClassValues))
        if oneClass["time"]:
            oneClass["timeInTheWeek"] = oneClass["time"].split("{")[0][:2]
            oneClass["timeInTheDay"] = oneClass["time"].split("{")[0][2:]
            oneClass["timeInTheTerm"] = oneClass["time"].split("{")[1][:-1]
        else:
            oneClass["timeInTheWeek"] = None
            oneClass["timeInTheDay"] = None
            oneClass["timeInTheTerm"] = None
        classes.append(oneClass)
    return {"classes": classes, "__VIEWSTATE": __VIEWSTATE}


def get__VIEWSTATE(response):
    html = response.content.decode("gb2312")
    soup = BeautifulSoup(html.decode("utf-8"), "html5lib")
    __VIEWSTATE = soup.findAll(name="input")[2]["value"]
    return __VIEWSTATE


def getGrade(response):
    html = response.content.decode("gb2312")
    soup = BeautifulSoup(html.decode("utf-8"), "html5lib")
    trs = soup.find(id="Datagrid1").findAll("tr")[1:]
    Grades = []
    for tr in trs:
        tds = tr.findAll("td")
        tds = tds[0:5] + tds[6:9]
        oneGradeKeys = ["year", "term", "classNo","name", "type", "credit","gradePonit","grade"]
        oneGradeValues = []
        for td in tds:
            oneGradeValues.append(td.string)
        oneGrade = dict((key, value) for key, value in zip(oneGradeKeys, oneGradeValues))
        Grades.append(oneGrade)
    return Grades

