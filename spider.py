# -*- coding: utf-8 -*-
# author: HuYong, MikeHuang

import os
import sys
import urllib
import datetime
import requests
import shutil
from lxml import etree
from identifyCode import *
from parseHtml import getSelectUrl, getClassScheduleFromHtml, getStudentInfor, get__VIEWSTATE, getGrade
from model import Student, db, ClassSchedule, Class, YearGrade, OneLessonGrade, TermGrade

class ZhengFangSpider:

    def __init__(self,student,baseUrl="http://jxgl.bjmu.edu.cn"):
        reload(sys)
        sys.setdefaultencoding("utf-8")
        self.trial = 0
        self.student = student
        self.baseUrl = baseUrl
        self.session = requests.session()
        self.session.headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.131 Safari/537.36'


    #含验证码登陆
    def login(self):
        MAXTRIAL =10
        self.trial += 1
        loginurl = self.baseUrl+"/default2.aspx"
        response = self.session.get(loginurl)
        selector = etree.HTML(response.content)
        input_values = selector.xpath('//*[@id="form1"]/input/@value')
        __VIEWSTATE = input_values[0]
        __VIEWSTATEGENERATOR = input_values[1]
        imgUrl = self.baseUrl+"/CheckCode.aspx?"
        imgresponse = self.session.get(imgUrl, stream=True)
        image = imgresponse.content
        DstDir = os.path.join(os.path.dirname(__file__), "code.jpg")
        print("保存验证码到：" + DstDir + "\n")
        try:
            with open(DstDir, "wb") as jpg:
                jpg.write(image)
        except IOError:
            print("IO Error\n")
        if self.trial == MAXTRIAL:
            code = raw_input("验证码是：")
        else:
            #　以下为验证码测试部分
            #shutil.move(DstDir, './test_images/' + code + '.jpg')
            loadTrainData()
            code = getAllOcr(DstDir)
        RadioButtonList1 = u"学生".encode('gb2312')
        data = {
            "__VIEWSTATE": __VIEWSTATE,
            "__VIEWSTATEGENERATOR": __VIEWSTATEGENERATOR,
            "txtUserName": self.student.studentnumber,
            "Textbox1": "",
            "TextBox2": self.student.password,
            "txtSecretCode": code,
            "RadioButtonList1": RadioButtonList1,
            "Button1": "",
            "lbLanguage": "",
            "hidPdrs": "",
            "hidsc": ""
        }
        # 登陆教务系统
        self.session.headers["Referer"] = self.baseUrl + '/'
        self.Loginresponse = self.session.post(loginurl, data=data)
        if self.Loginresponse.url == u"http://jxgl.bjmu.edu.cn/xs_main.aspx?xh=" + self.student.studentnumber:
            return self.Loginresponse
        elif self.trial < MAXTRIAL:
            return self.login()
        else:
            return None


    #获取学生基本信息
    def getStudentBaseInfo(self):
        self.session.headers['Referer'] = self.baseUrl+"/xs_main.aspx?xh="+self.student.studentnumber
        url = getSelectUrl(self.Loginresponse, u"个人信息")
        response = self.session.get(self.baseUrl + '/' + url)
        d = getStudentInfor(response)
        self.student.idCardNumber =d["idCardNumber"]
        self.student.name =d["name"]
        self.student.urlName = urllib.quote_plus(str(d["name"].encode('gb2312')))
        self.student.sex =d["sex"]
        self.student.enterSchoolTime =d["enterSchoolTime"]
        self.student.birthsday =d["birthsday"]
        self.student.highschool =d["highschool"]
        self.student.nationality =d["nationality"]
        self.student.hometown =d["hometown"]
        self.student.politicsStatus =d["politicsStatus"]
        self.student.college =d["college"]
        self.student.major =d["major"]
        self.student.classname =d["classname"]
        self.student.gradeClass =d["gradeClass"]
        self.student.save()
        return 'ok'


    #获取学生课表
    def getClassSchedule(self):
        self.session.headers['Referer'] = self.baseUrl+"/xs_main.aspx?xh="+self.student.studentnumber
        urlsuffix = getSelectUrl(self.Loginresponse, u'学生选课情况查询')
        url = self.baseUrl + '/' + urlsuffix
        response = self.session.get(url)
        parsedict = getClassScheduleFromHtml(response)
        __VIEWSTATE = parsedict["__VIEWSTATE"]
        __EVENTTARGET = "ddlXQ"
        year = int(self.student.gradeClass)
        term = 1
        today = datetime.date.today()
        while today.year>year or (today.year==year and today.month>=7 and term==1):
            data = {
                "__EVENTTARGET": __EVENTTARGET,
                "__EVENTARGUMENT": "",
                "__VIEWSTATEGENERATOR" : "FDD5582C",
                "__VIEWSTATE": __VIEWSTATE,
                "ddLXN": str(year)+"-"+str(year+1),
                "ddLXQ": str(term),
            }
            self.session.headers['Referer'] = url
            response = self.session.post(url,data)
            print "正在获取"+str(year)+"-"+str(year+1)+"学年第"+str(term)+"学期课表"
            parsedict = getClassScheduleFromHtml(response)
            if parsedict != None:
                classes = parsedict["classes"]
            else:
                continue
            __VIEWSTATE = getClassScheduleFromHtml(response)["__VIEWSTATE"]
            classSchedule = ClassSchedule(student=self.student,year=str(year)+"-"+str(year+1),term=term)
            classSchedule.save()
            for each in classes:
                #debug
                #try:
                oneClass = Class(schedule=classSchedule , selectClassCode=each["selectClassCode"],
                             classNo=each["classNo"],name=each["name"], type=each["type"],
                             Compulsory= each["Compulsory"],teacher=each["teacher"], point=each["point"],
                             totalTimeInWeek=each["totalTimeInWeek"], timeInTheWeek = each["timeInTheWeek"],
                             timeInTheDay = each["timeInTheDay"], timeInTheTerm=each["timeInTheTerm"],
                             location=each["location"])
                oneClass.save()
                #except KeyError as e:
                    #print each
                    #raise KeyError
            term = term + 1
            if term>2:
                term = 1
                year = year+1
                __EVENTTARGET = "ddlXQ"
            else:
                __EVENTTARGET = "ddlXN"
        return 'ok'


    # 获取学生绩点
    def getStudentGrade(self):
        urlsuffix = getSelectUrl(self.Loginresponse, u'成绩查询')
        url = self.baseUrl + '/' + urlsuffix
        self.session.headers['Referer'] = self.baseUrl + "/xs_main.aspx?xh=" + self.student.studentnumber
        response = self.session.get(url)
        __VIEWSTATE = get__VIEWSTATE(response)
        self.session.headers['Referer'] = url
        data = {
            "__EVENTTARGET":"",
            "__EVENTARGUMENT":"",
            "__VIEWSTATE":__VIEWSTATE,
            "__VIEWSTATEGENERATOR" : "9727EB43",
            'hidLanguage':"",
            "ddlXN":"",
            "ddlXQ":"",
            "ddl_kcxz":"",
            "btn_zcj" : u"历年成绩".encode('gb2312', 'replace')
        }
        response = self.session.post(url,data=data)
        grades = getGrade(response)
        for onegrade in grades:
            year = onegrade["year"]
            term = onegrade["term"]
            classNo = onegrade["classNo"]
            try:
                yearGrade = YearGrade.get(YearGrade.year == year , YearGrade.student == self.student)
            except:
                yearGrade = YearGrade(year=year,student=self.student)
                yearGrade.save()
            try:
                termGrade = TermGrade.get(TermGrade.year == yearGrade , TermGrade.term == int(term))
            except:
                termGrade = TermGrade(year = yearGrade ,term = int(term))
                termGrade.save()
            try:
                lesson = Class.get(Class.classNo == classNo)
            except:
                schedule = ClassSchedule.get(ClassSchedule.year == year, ClassSchedule.term == term)
                lesson = Class(schedule=schedule, classNo=classNo, name=onegrade["name"]
                              ,type=onegrade["type"], point=float(onegrade["credit"]))
                lesson.save()

            try:
                gradePoint = float(onegrade["gradePonit"])
            except:
                gradePoint = None

            try:
                grade = float(onegrade["grade"])
            except:
                grade = None

            oneLessonGrade = OneLessonGrade(lesson=lesson, term=termGrade, gradePoint=gradePoint,
                                             grade=grade)
            oneLessonGrade.save()
        return 'ok'


    # 计算每学期，每学年的绩点
    def calculateOneTermAndOneYearGPA(self):
        years = self.student.grades
        for year in years:
            terms = year.terms
            for term in terms:
                sumCredit = 0.0
                sumGrade = 0.0
                grades = term.lessonsGrades
                for grade in grades:
                        if grade.gradePoint == None:
                            continue
                        credit = OneLessonGrade.select(OneLessonGrade, Class)\
                            .join(Class).where(Class.id == grade.lesson_id).get().lesson.point
                        sumGrade = sumGrade +(credit * grade.gradePoint)
                        sumCredit = sumCredit + credit
                termGPA = round((sumGrade/sumCredit), 2)
                term.termGPA = termGPA
                term.termCredit = sumCredit
                term.save()
            sumGrade = 0.0
            sumCredit = 0.0
            for term in terms:
                sumGrade += term.termGPA*term.termCredit
                sumCredit += term.termCredit
            year.yearGPA = round((sumGrade/sumCredit), 2)
            year.yearCredit = sumCredit
            year.save()
        return 'ok'


if __name__ == "__main__":

    # 连接数据库，建立数据表
    try:
        db.connect()
        db.create_tables([Student, ClassSchedule,Class,YearGrade,TermGrade,OneLessonGrade])
    except Exception:
        print Exception.message

    # 查找学生，若不存在则创建账号
    try:
        student = Student.get(Student.studentnumber == "xxxxxxxx")
    except Exception, e:
        student = Student(studentnumber="xxxxxxxx", password="xxxxxxxxx")#用自己的教务系统账号密码
        student.save()

    spider = ZhengFangSpider(student) # 实例化爬虫
    spider.login()
    if student.name is None:
        spider.getStudentBaseInfo()
    spider.getStudentGrade()
    spider.calculateOneTermAndOneYearGPA()
    spider.getClassSchedule()

