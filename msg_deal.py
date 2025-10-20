#msg_deal.py
import http.client
import hashlib
import urllib
from urllib import request, error
import time
import re
import json
import math
import socket
import os
import traceback
import random
import openai
import requests

import scrlib.mlib as lib
from scrlib.imagedb import ImgDB
import scrlib.ybtext as ybtext
import scrlib.zhouyi as yi

class Message:
    date_jieqi = {}
    oldimg_lst = {}
    lastimgfile = {}
    cur_send_user = ""
    imgdb = ImgDB()

    def __init__(self, config={}):
        self.config = config
        if os.path.exists('jieqi.json'):
            self.date_jieqi = json.load(open('jieqi.json'))
        else:
            json.dump(self.date_jieqi, open('jieqi.json', 'w'))
        if os.path.exists('tags.json'):
            self.map_tags = json.load(open('tags.json', encoding='utf-8'))
            self.map_tags.update(ybtext.map_tags)
        else:
            json.dump(ybtext.map_tags, open(
                'tags.json', 'w', encoding='utf-8'))
        # self.pic_path = "/home/sunjianpei/apache-tomcat-9.0.65/webapps/sumi/pic/"
        self.pic_path = "./static/pic/"
        lib.check_path(os.path.join(self.pic_path , "sample/"))
        lib.check_path(os.path.join(self.pic_path , "preview/"))

        tmplist = list(self.imgdb.get_sendlog_month())
        # print(len(tmplist))
        for one in tmplist:
            if not one[2] in self.oldimg_lst:
                self.oldimg_lst[one[2]] = []
            self.oldimg_lst[one[2]].append(one[0])
        #print("oldimg_lst", self.oldimg_lst)
            
        if 'chatgpt' in config and config['chatgpt']['apikey']:
            openai.api_key = config['chatgpt']['apikey']


    def deal(self, msg, sid = '0', bUser = True) :
        reply = "这是一个默认回复。"
        nextorder = None
        if re.match('^干支[:：]?(.*)', msg):
            mt = re.match('干支[:：]?(.*)', msg)
            org = mt.group(1)
            reply = self.ganzhi(org)[0]
        elif re.match('下个吉时', msg):
            reply = self.nextqmds()
        elif re.match('^翻译\\S*[:：].*', msg):
            mt = re.match('^翻译(\\S*)[:：](.*)', msg)
            org = mt.group(2)
            lan = mt.group(1)
            reply = self.translate_zh(org, lan)
        elif re.match('超级翻译[:：].*', msg):
            mt = re.match('^超级翻译[:：](.*)', msg)
            org = mt.group(1)
            reply = self.translate_loop(org)
        elif re.match('转为\\S+[:：].+', msg):
            mt = re.match('转为(\\S+?)[:：](.+)', msg)
            org = mt.group(2)
            lan = mt.group(1)
            reply = self.translate_assign(org, lan, msg)
        elif re.search('新图', msg):
            mt = re.search('(\\S*)新图\\*(\\d+)', msg)
            key = ""
            remain = 1
            if mt:
                key = mt.group(1)
                remain = min(int(mt.group(2)), 10)
            reply = ""
            if bUser:
                self.stopimg = False
            lib.log(f'等待发送新图: {remain}')
            
            reply += self.send_img(1, sid, msg)
            if remain > 1 and not self.stopimg:
                reply += f"\n剩余{remain - 1}张"
                nextorder = f'{key}新图*{remain - 1}'
        elif re.search('热图', msg):
            mt = re.search('(\\S*)热图\\*(\\d+)', msg)
            key = ""
            remain = 1
            if mt:
                key = mt.group(1)
                remain = min(int(mt.group(2)), 10)
            reply = ""
            if bUser:
                self.stopimg = False
            lib.log(f'等待发送热图: {remain}')
            
            reply += self.send_img(2, sid, msg)
            if remain > 1 and not self.stopimg:
                reply += f"\n剩余{remain - 1}张"
                nextorder = f'{key}热图*{remain - 1}'
        elif re.search('宽高比\\d+([\\./]\\d+)?图', msg):
            strRatio = re.search('宽高比(.*)图', msg).group(1)
            ratio = float(eval(strRatio))
            mt = re.search('(\\S*)宽高比.*图\\*(\\d+)', msg)
            key = ""
            remain = 1
            if mt:
                key = mt.group(1)
                remain = min(int(mt.group(2)), 10)
            reply = ""
            if bUser:
                self.stopimg = False
            lib.log(f'等待发送宽高比{strRatio}图: {remain}')
            
            reply += self.send_img(2, sid, msg, ratio)
            if remain > 1 and not self.stopimg:
                reply += f"\n剩余{remain - 1}张"
                nextorder = f'{key}宽高比{strRatio}图*{remain - 1}'
        elif re.match('^收藏', msg):
            reply = self.setImgFavor(sid, msg)
        elif re.match('^删除.*jpg', msg):
            mt = re.search('删除[:：]?(.*\\.jpg)', msg)
            filename = mt.group(1)
            reply = self.deleteimg(sid, filename)
        elif re.match('^停+$', msg):
            self.stopimg = True
            reply = ybtext.msg_stop[0]
        elif re.match('^今日头条', msg):
            reply = self.get_tophub()
        elif re.match('^藏[头尾中增减]诗[:：]\\S+', msg):
            reply = self.versify(msg)
        elif re.match('倒置:', msg):
            mt = re.match('倒置:(.*)', msg)
            org = mt.group(1)
            reply = self.inversion(org)
        elif re.match('占卜[:：]?(.*)', msg):
            mt = re.match('占卜[:：]?(.*)', msg)
            org = mt.group(1)
            reply= self.liuyao(org)
        elif re.match("\\S+是什么垃圾", msg):
            mt = re.match('(\\S+)是什么垃圾', msg)
            org = mt.group(1)
            reply = self.garbage_classify(org)
        elif re.match(r"^历史上的((今天)|(\d{4}))", msg):
            mt = re.match(r"历史上的(\d{4})", msg)
            if mt:
                org = mt.group(1)
                reply = self.InHis(org)
            else:
                reply = self.TodayInHis()
        elif re.match('^执行[:：](.*)', msg):
            mt = re.match('执行[:：](.*)', msg)
            org = mt.group(1)
            reply = self.cast_as_eval(org)
        elif self.config['chatgpt']['enable'] and not re.match("^\\s*$", msg):
            # reply = self.chat_gpt(msg, id, 2)
            reply = self.deepseek_chat(msg, id)

        return reply, nextorder

    def getjieqi(self, date_q) -> str:
        ct = 0
        idate = date_q
        jieqi = ""
        myurl = "http://api.tianapi.com/txapi/lunar/index"
        key = self.config['tianapi_key']
        while ct < 30:
            if idate not in self.date_jieqi:
                iurl = myurl + '?key=' + key + '&date=' + idate
                f = urllib.request.urlopen(iurl, timeout=8)

                result_all = f.read()
                result = json.loads(result_all)
                if result['code'] != 200:
                    lib.log(f'fail to get jieqi, wrong url:{ iurl}')
                    lib.log(f'result:{result}')
                    break
                else:
                    hllist = result['newslist'][0]
                    self.date_jieqi[idate] = hllist['jieqi']
                time.sleep(1)
            if self.date_jieqi[idate] != '':
                jieqi = self.date_jieqi[idate]
                break
            idate = time.strftime(
                    "%Y-%m-%d", time.localtime(time.mktime(time.strptime(idate, "%Y-%m-%d")) - 24 * 3600))
            ct += 1
        json.dump(self.date_jieqi, open('jieqi.json', 'w'))
        return jieqi

    def ganzhi(self, org) -> str:
        httpClient = None

        myurl = "http://api.tianapi.com/txapi/lunar/index"
        key = self.config['tianapi_key']
        date_q = org.strip()
        hour = 0
        min = 0
        sec = 0

        if date_q == "":
            date_q = time.strftime("%Y-%m-%d")
            hour = (int)(time.strftime("%H"))
            min = (int)(time.strftime("%M"))
            sec = (int)(time.strftime("%S"))
        elif re.match("\\d+-\\d+-\\d+ \\d+:\\d+:\\d+", date_q):
            mt = re.match("(\\d+-\\d+-\\d+) (\\d+):(\\d+):(\\d+)", date_q)
            date_q = mt.group(1)
            hour = (int)(mt.group(2))
            min = (int)(mt.group(3))
            sec = (int)(mt.group(4))
        elif re.match("[+-]\\d+(\\.\\d+)?", date_q):
            mt = re.match("([+-])(\\d+(\\.\\d+)?)", date_q)
            timestamp_add = (float)(mt.group(2)) * \
                (mt.group(1) == '+' and 3600 or -3600)
            # print(f'timestamp_add:{timestamp_add}')
            target_time = time.localtime(time.time() + timestamp_add)
            date_q = time.strftime("%Y-%m-%d", target_time)
            hour = (int)(time.strftime("%H", target_time))
            # print(f'date_q:{date_q}, hour:{hour}')
        else:
            return [ybtext.msg_illegal[5], ]
        if hour >= 23:
            date_q = time.strftime("%Y-%m-%d", time.localtime(time.mktime(
                time.strptime(date_q, "%Y-%m-%d")) + (hour - 23 + 24) * 3600))
            hour = max(hour - 24, 0)

        turl = myurl + '?key=' + key + '&date=' + date_q

        asw = ybtext.msg_notfind[2]
        ifqmds = False
        ifbad = False
        try:
            lib.log(turl)
            f = urllib.request.urlopen(turl, timeout=8)

            result_all = f.read()
            result = json.loads(result_all)
            if result['code'] != 200:
                return ybtext.msg_illegal[5]
            hllist = result['newslist'][0]

            gzyear = hllist['tiangandizhiyear']
            gzmonth = hllist['tiangandizhimonth']
            gzday = hllist['tiangandizhiday']
            self.date_jieqi[date_q] = hllist['jieqi']

            gday2firstgz = {"甲": 0, "乙": 2, "丙": 4, "丁": 6,
                            "戊": 8, "己": 0, "庚": 2, "辛": 4, "壬": 6, "癸": 8}
            gday = gzday[0:1]
            zday = gzday[1:2]
            gan_zishi = gday2firstgz[gday]
            dizhi_time = (math.floor((hour+1)/2)) % 12
            tiangan_time = (gan_zishi + dizhi_time) % 10
            gztime = ybtext.tiangan[tiangan_time] + ybtext.dizhi[dizhi_time]
            asw = ybtext.msg_ganzhi[0].format(gzyear, gzmonth, gzday, gztime)

            # compute qimendunjia
            jieqi = self.getjieqi(date_q)

            tmp_dz = ybtext.dizhi.index(zday) - ybtext.tiangan.index(gday) % 5
            tmp_dz = tmp_dz if tmp_dz >= 0 else tmp_dz+12

            yuan = tmp_dz % 3
            yuan = 0 if yuan == 0 else 3-yuan
            liangyi = ""
            qiju = 0
            if jieqi in ybtext.jieqi_yang:
                liangyi = "阳"
                qiju = (ybtext.jieqi_yang[jieqi] + 6*yuan - 1) % 9 + 1
            elif jieqi in ybtext.jieqi_yin:
                liangyi = "阴"
                qiju = (ybtext.jieqi_yin[jieqi] + 3*yuan - 1) % 9 + 1
            dipan = ["囗"]*10
            ct = 4
            cur_gong = qiju  # 当前宫1-9
            step_gong = 1 if liangyi == "阳" else -1
            while ct > 0:
                if ct > 9:
                    ct = 3
                dipan[cur_gong] = ybtext.tiangan[ct]

                if ct >= 4:
                    ct += 1
                else:
                    ct -= 1
                cur_gong += step_gong
                if cur_gong > 9:
                    cur_gong -= 9
                elif cur_gong < 1:
                    cur_gong += 9
            id_xunshou = dizhi_time - \
                tiangan_time if dizhi_time >= tiangan_time else dizhi_time + 12 - tiangan_time
            #print("id_xunshou, ybtext.dizhi[id_xunshou]",id_xunshou, ybtext.dizhi[id_xunshou])
            dunjia = {0: 4, 10: 5, 8: 6, 6: 7, 4: 8, 2: 9}
            id_dun = dunjia[id_xunshou]
            gong_zhifu = dipan.index(ybtext.tiangan[id_dun])
            zhifu = ybtext.jiuxing[gong_zhifu]
            zhishi = ybtext.bamen[gong_zhifu]
            #print("id_dun,dun,gong_zhifu",id_dun, ybtext.tiangan[id_dun], gong_zhifu)
            gong_cur_fu = dipan.index(
                ybtext.tiangan[tiangan_time]) if tiangan_time != 0 else gong_zhifu
            gong_cur_shi = (gong_zhifu + tiangan_time - 1) % 9 + \
                1 if liangyi == '阳' else (
                    gong_zhifu + 9 - tiangan_time - 1) % 9 + 1
            # print("gong_cur_fu,gong_cur_shi",gong_cur_fu,gong_cur_shi)

            #pos_gong = [4,9,2,3,5,7,8,1,6]
            next_gong = {1: 8, 2: 7, 3: 4, 4: 9, 5: 0, 6: 1, 7: 6, 8: 3, 9: 2}
            ct = 0
            tianpan = ["囗"]*10
            igong = gong_cur_fu if gong_cur_fu != 5 else 2
            ixing = gong_zhifu if gong_zhifu != 5 else 2
            while ct < 8:
                tianpan[igong] = ybtext.jiuxing[ixing]
                igong = next_gong[igong]
                ixing = next_gong[ixing]
                ct += 1
            tianpan[5] = ybtext.jiuxing[5]
            ct = 0
            tianpan2 = dipan.copy()
            igong = gong_cur_fu if gong_cur_fu != 5 else 2
            ixing = gong_zhifu if gong_zhifu != 5 else 2
            while ct < 8:
                tianpan2[igong] = dipan[ixing]
                igong = next_gong[igong]
                ixing = next_gong[ixing]
                ct += 1
            ct = 0
            renpan = ["囗"]*10
            igong = gong_cur_shi if gong_cur_shi != 5 else 2
            imen = gong_zhifu if gong_zhifu != 5 else 2
            while ct < 8:
                renpan[igong] = ybtext.bamen[imen]
                igong = next_gong[igong]
                imen = next_gong[imen]
                ct += 1

            ct = 0
            shenpan = ["囗"]*10
            igong = gong_cur_fu if gong_cur_fu != 5 else 2
            ishen = 1
            shenjiang = ybtext.shen_yang if liangyi == "阳" else ybtext.shen_yin
            while ct < 8:
                shenpan[igong] = shenjiang[ishen]
                igong = next_gong[igong]
                ishen = next_gong[ishen]
                ct += 1
            shenpan[5] = shenjiang[5]
            asw += "\t" + ybtext.msg_bagua[0].format(jieqi, ybtext.yuan[yuan])
            asw += "\n" + ybtext.msg_bagua[1].format(liangyi, qiju)
            asw += "\n" + ybtext.msg_bagua[3].format(zhifu, zhishi)
            asw += "\n" + ybtext.msg_bagua[2].format(
                dipan[4], dipan[9], dipan[2], dipan[3], dipan[5], dipan[7], dipan[8], dipan[1], dipan[6])
            asw += "\n" + ybtext.msg_bagua[4].format(tianpan2[4]+tianpan[4], tianpan2[9]+tianpan[9], tianpan2[2]+tianpan[2], tianpan2[3]+tianpan[3],
                                                     tianpan2[5]+tianpan[5], tianpan2[7]+tianpan[7], tianpan2[8]+tianpan[8], tianpan2[1]+tianpan[1], tianpan2[6]+tianpan[6])
            asw += "\n" + ybtext.msg_bagua[5].format(
                renpan[4], renpan[9], renpan[2], renpan[3], renpan[5], renpan[7], renpan[8], renpan[1], renpan[6])
            asw += "\n" + ybtext.msg_bagua[6].format(shenpan[4], shenpan[9], shenpan[2],
                                                     shenpan[3], shenpan[5], shenpan[7], shenpan[8], shenpan[1], shenpan[6])

            jxlist = set()
            jimen = (ybtext.bamen[1], ybtext.bamen[8], ybtext.bamen[6])
            sanqi = (ybtext.tiangan[1], ybtext.tiangan[2], ybtext.tiangan[3])

            def judge(gong, diqi, tianqi, tianxing, men, shen) -> str:
                # print("gong,diqi,tianqi,tianxing,men,shen",gong,diqi,tianqi,tianxing,men,shen)
                ifqmds = False
                ifbad = False
                if (diqi in sanqi or tianqi in sanqi) and men in jimen and (men == zhishi or tianxing == zhifu):
                    lib.log(f'qmds:{gong}')
                    #print(gong, diqi, tianqi, tianxing, men, shen)
                    jxlist.add(ybtext.msg_qmdj[0].format(gong))
                    ifqmds = True
                if diqi == ybtext.tiangan[3] and men == zhishi:
                    jxlist.add(ybtext.msg_qmdj[1])
                if men == zhishi and gong == gong_zhifu:
                    jxlist.add(ybtext.msg_qmdj[2])
                    ifbad = True
                if men == zhishi and (gong if gong != 5 else 2) + (gong_zhifu if gong_zhifu != 5 else 2) == 10:
                    jxlist.add(ybtext.msg_qmdj[3])
                    ifbad = True
                if tianxing == zhifu and gong == gong_zhifu:
                    jxlist.add(ybtext.msg_qmdj[4])
                    ifbad = True
                if tianxing == zhifu and (gong if gong != 5 else 2) + (gong_zhifu if gong_zhifu != 5 else 2) == 10:
                    jxlist.add(ybtext.msg_qmdj[5])
                    ifbad = True
                mu = {ybtext.tiangan[1]: 2,
                      ybtext.tiangan[2]: 6, ybtext.tiangan[3]: 8}
                if gday in sanqi and gday == tianqi and gong == mu[tianqi]:
                    jxlist.add(ybtext.msg_qmdj[6])
                    ifbad = True
                shimu = [ybtext.tiangan[2]+ybtext.dizhi[10], ybtext.tiangan[8]+ybtext.dizhi[4], ybtext.tiangan[3]+ybtext.dizhi[1],
                         ybtext.tiangan[9]+ybtext.dizhi[7], ybtext.tiangan[4]+ybtext.dizhi[10], ybtext.tiangan[5]+ybtext.dizhi[1]]
                if gztime in shimu:
                    jxlist.add(ybtext.msg_qmdj[7])
                    ifbad = True
                wbys = {ybtext.tiangan[0]: ybtext.dizhi[6], ybtext.tiangan[1]: ybtext.dizhi[5], ybtext.tiangan[2]: ybtext.dizhi[4], ybtext.tiangan[3]: ybtext.dizhi[3], ybtext.tiangan[4]: ybtext.dizhi[2],
                        ybtext.tiangan[5]: ybtext.dizhi[1], ybtext.tiangan[6]: ybtext.dizhi[0], ybtext.tiangan[7]: ybtext.dizhi[9], ybtext.tiangan[8]: ybtext.dizhi[8], ybtext.tiangan[9]: ybtext.dizhi[7]}
                if wbys[gday] == ybtext.dizhi[dizhi_time]:
                    jxlist.add(ybtext.msg_qmdj[8])
                    ifbad = True
                if tianqi in sanqi and men in jimen:
                    if shen == ybtext.shen_yang[3]:
                        jxlist.add(ybtext.msg_qmdj[9].format(gong))
                    if shen == ybtext.shen_yang[7]:
                        jxlist.add(ybtext.msg_qmdj[10].format(gong))
                    if shen == ybtext.shen_yang[4]:
                        jxlist.add(ybtext.msg_qmdj[11].format(gong))
                if tianqi == ybtext.tiangan[2] and men == ybtext.bamen[8]:
                    if shen == ybtext.shen_yang[6]:
                        jxlist.add(ybtext.msg_qmdj[12].format(gong))
                    elif diqi == ybtext.tiangan[3]:
                        jxlist.add(ybtext.msg_qmdj[13].format(gong))
                if tianqi == ybtext.tiangan[1]:
                    if men == ybtext.bamen[6] and diqi == ybtext.tiangan[5]:
                        jxlist.add(ybtext.msg_qmdj[14].format(gong))
                    elif men == ybtext.bamen[1] and gong in (8, 4):
                        jxlist.add(ybtext.msg_qmdj[15].format(gong))
                    elif men == ybtext.bamen[4] and shen == ybtext.shen_yang[7]:
                        jxlist.add(ybtext.msg_qmdj[16].format(gong))
                    elif men in jimen:
                        if gong == 4:
                            jxlist.add(ybtext.msg_qmdj[17].format(gong))
                        if diqi == ybtext.tiangan[7]:
                            jxlist.add(ybtext.msg_qmdj[18].format(gong))
                        if gong == 1:
                            jxlist.add(ybtext.msg_qmdj[19].format(gong))
                if tianqi == ybtext.tiangan[3] and men == ybtext.bamen[1] and shen == ybtext.shen_yang[3]:
                    jxlist.add(ybtext.msg_qmdj[20].format(gong))
                return ifqmds, ifbad
            for i in range(1, 10):
                idiqi = dipan[i]
                itianqi = tianpan2[i]
                itianxing = tianpan[i]
                imen = renpan[i]
                ishen = shenpan[i]
                if i == 5:
                    itianqi = tianpan2[2]
                    itianxing = tianpan[2]
                affix = judge(i, idiqi, itianqi, itianxing, imen, ishen)
                ifqmds = ifqmds or affix[0]
                ifbad = ifbad or affix[1]
                if itianxing == ybtext.jiuxing[2]:
                    affix = judge(
                        i, idiqi, tianpan2[5], tianpan[5], imen, ishen)
                    ifqmds = ifqmds or affix[0]
                    ifbad = ifbad or affix[1]

            asw += "\n" + ",".join(jxlist)

        except Exception as e:
            lib.log(e)
            if isinstance(e, socket.timeout):
                asw = self.random_str(ybtext.msg_timeout)
        finally:
            if httpClient:
                httpClient.close()
        return asw, ifqmds and (not ifbad), '{} {:0>2d}:00:00'.format(date_q, hour)
    def nextqmds(self) -> str:
        asw = ''
        for i in range(0, 48, 2):
            _, ifqmds, ndate = self.ganzhi('+' + str(i))
            # print(ifqmds)
            if ifqmds:
                asw = asw + \
                    '<span style="cursor:pointer;" onClick="coverInput(\'' + ybtext.msg_ganzhi[1] + str(ndate) + \
                    '\')">' + str(ndate) + '</span>' + '\n'
            time.sleep(1)
        if asw == '':
            return ybtext.msg_notfind[3]
        else:
            return asw
    def liuyao(self, org) :
        org = org.strip()
        if org != '':
            sTime = time.strftime("%Y-%m-%d %H")
            seed = f'{sTime}:{org}'
        else:
            seed = time.strftime("%Y-%m-%d %H:%M:%S")
        asw = yi.yigua(seed)
        return asw
        
        
    def random_str(self, str_list: list) -> str:
        n = 0
        n = math.floor(random.random() * len(str_list))
        return str_list[n]

    def random_dict(self, str_dict: dict) -> str:
        new_dict = {}
        max_weidth = 0
        for ikey in str_dict:
            max_weidth = max_weidth + str_dict[ikey]
            new_dict[ikey] = max_weidth
        n = math.floor(random.random() * max_weidth)
        for ikey in new_dict:
            if new_dict[ikey] > n:
                return ikey
        return "error"
    
    def garbage_classify(self, org) -> str:

        myurl = 'http://api.tianapi.com/txapi/lajifenlei/index'
        key = self.config['tianapi_key']
        name = org
        myurl = myurl + '?key=' + key + '&word=' + \
            urllib.parse.quote(name, 'uft-8')

        asw = "不知道" + org + "是什么垃圾"

        try:
            f = urllib.request.urlopen(myurl)

            result_all = f.read()
            result = json.loads(result_all)
            if result['code'] == 200:
                re_list = result['newslist']
                asw_arr = []
                for item in re_list:
                    if item['name'] == name:
                        asw_arr.clear()
                        asw_arr.append(
                            f'{item["name"]} 是 {ybtext.msg_garbage[item["type"]]}')
                        break
                    else:
                        asw_arr.append(
                            f'{item["name"]} 是 {ybtext.msg_garbage[item["type"]]}')
                asw = "\n".join(asw_arr)
            else:
                x = 0
                for s in bytes(name, encoding="utf8"):
                    x = x + s
                asw = "我觉得" + name + "是" + ybtext.msg_garbage[x % 4]
        except Exception as e:
            print(e)
        return asw
    
    def translate_zh(self, org, lan) -> str:
        appid = self.config['baidufanyi_appid']
        secretKey = self.config['baidufanyi_key']

        httpClient = None
        myurl = 'http://api.fanyi.baidu.com/api/trans/vip/translate'

        fromLang = 'auto'  # 原文语种
        if re.match('^粤', lan):
            fromLang = 'yue'
        if re.match('^文言文', lan):
            fromLang = 'wyw'
        toLang = 'zh'  # 译文语种
        salt = random.randint(32768, 65536)
        q = org
        sign = appid + q + str(salt) + secretKey
        sign = hashlib.md5(sign.encode()).hexdigest()
        myurl = myurl + '?appid=' + appid + '&q=' + urllib.parse.quote(
            q) + '&from=' + fromLang + '&to=' + toLang + '&salt=' + str(salt) + '&sign=' + sign

        asw = '未查到结果'

        try:
            httpClient = http.client.HTTPConnection('api.fanyi.baidu.com')
            httpClient.request('GET', myurl)

            # response是HTTPResponse对象
            response = httpClient.getresponse()
            result_all = response.read().decode("utf-8")
            result = json.loads(result_all)
            asw = result['trans_result'][0]['dst']
            lan_from = ybtext.lang.get(result['from'], 'Other')
            asw = result['trans_result'][0]['dst'] + " (" + lan_from + ")"

        except Exception as e:
            print(e)
        finally:
            if httpClient:
                httpClient.close()
        return asw

    def transapi(self, q, lan, froml='auto') -> str:
        appid = self.config['baidufanyi_appid']
        secretKey = self.config['baidufanyi_key']
        httpClient = None
        myurl = 'http://api.fanyi.baidu.com/api/trans/vip/translate'

        fromLang = froml  # 原文语种

        salt = random.randint(32768, 65536)
        toLang = lan
        sign = appid + q + str(salt) + secretKey
        sign = hashlib.md5(sign.encode()).hexdigest()
        myurl = myurl + '?appid=' + appid + '&q=' + urllib.parse.quote(
            q) + '&from=' + fromLang + '&to=' + toLang + '&salt=' + str(salt) + '&sign=' + sign
        
        ret = ""
        
        try:
            httpClient = http.client.HTTPConnection('api.fanyi.baidu.com')
            httpClient.request('GET', myurl)
            for i in range(0,2):
                response = httpClient.getresponse()
                result_all = response.read().decode("utf-8")
                result = json.loads(result_all)
                if 'trans_result' in result:
                    ret = result['trans_result'][0]['dst']
                    break
                else:
                    lib.log("translate_api return error:", result)
                    time.sleep(0.5)
        except Exception as e:
            lib.log("translate_api error", result)
        finally:
            if httpClient:
                httpClient.close()
        return ret
    def translate_loop(self, org) -> str:
        # lan_lst = ["en", "jp", "kor", "fra", "spa", "ara", "ru", "pt", "de", "it", 
        #            "el", "nl", "pl", "bul", "est", "dan", "fin", "cs", "rom", "slo", "swe", "hu"]
        lan_lst = ["en", "jp", "kor", "fra", "spa", "ara", "ru", "pt", "de", "it", 
                    "el", "nl", "pl", "dan", "fin", "cs", "rom", "swe"]
        que = org
        lanFrom = "auto"
        asw = ""
        for lan in lan_lst:
            que = self.transapi(que, lan, lanFrom)
            untrans = self.transapi(que, 'zh', lan)
            asw += f'{ybtext.lang.get(lan)}:{que} | 汉语:{untrans}' + '\n'
            lanFrom = lan
        asw += self.transapi(que, 'zh', lanFrom)
        return asw

    def translate_assign(self, org, lan, msg) -> str:
        if re.search('日', lan):
            toLang = 'jp'  # 译文语种
        elif re.search('英', lan):
            toLang = 'en'
        elif re.search('德', lan):
            toLang = 'de'
        elif re.search('俄', lan):
            toLang = 'ru'
        elif re.search('法', lan):
            toLang = 'fra'
        elif re.search('文言文', lan):
            toLang = 'wyw'
        elif re.search('粤', lan):
            toLang = 'yue'
        # elif re.search('语音', lan):
        #     return self.to_voice(org, msg)
        else:
            return '不支持语种'
        
        asw = self.transapi(org, toLang)
        
        return asw
    
    def pinyin(self, word) -> str:
        import pypinyin
        s = ''
        for i in pypinyin.pinyin(word, style=pypinyin.NORMAL):
            s += ''.join(i)
        return s
    def setImgFavor(self, sid, msg):
        sender = str(sid)
        print(sender)
        filename = ""
        ma = re.match('^收藏(\S+)', msg)
        if ma:
            filename = ma.group(1)
        elif sender in self.lastimgfile:
            filename = self.lastimgfile[sender]
        else:
            return ybtext.msg_setfavor[0]
        
        preview_path = 'static/pic/preview/'
        filelist = os.listdir(preview_path)
        if filename in filelist:
            self.imgdb.addFavor(sid, filename)
            return ybtext.msg_setfavor[1].format(filename)
        else:
            return ybtext.msg_notexists[4]

    def send_img(self, searchtype, id, message, ratio=0):
        def write_dblog(filename, id):
            dt = time.strftime("%Y-%m-%d")
            #print("dt:", dt)

            sender = str(id)
            msg_type = "default"
            self.imgdb.insert(filename, msg_type, sender, dt) 

            self.oldimg_lst[sender].append(filename)
            # print(f"record {filename}")
            self.lastimgfile[sender] = filename
        self.cur_send_user = str(id)
        tmp_msg = {}
        ban = False
        mode = searchtype == 2 and 'yande_hot' or 'yande'
        tmp_msg, ban = self.image_api(mode, message, ratio)

        if type(tmp_msg) is dict and 'data' in tmp_msg:
            write_dblog(tmp_msg['data']['file'], id)

        tips = tmp_msg['data']['file'] if 'data' in tmp_msg else ''
        if 'data' in tmp_msg:
            if 'delay' in tmp_msg['data']:
                delay = tmp_msg['data']['delay']
                if delay >= 24:
                    delay = math.floor(delay / 24)
                    delay = str(delay) + (" days" if delay > 1 else " day")
                else:
                    delay = str(delay) + (" hours" if delay > 1 else " hour")
                tips += ('\n' + ybtext.msg_delay[0].format(delay))
            if 'size' in tmp_msg['data']:
                file_size = tmp_msg['data']['size']
                file_size = round(file_size/(1024 * 1024), 2)
                if file_size < 5:
                    tips += ('\n' + ybtext.msg_size[0].format(file_size))
                else:
                    tips += ('\n' + ybtext.msg_size[1].format(file_size))
            # if ban:
            #     imginfo = ybtext.msg_skip[4].format(tmp_msg['data']['file'], tmp_msg['data']['source'])
            if 'skip' in tmp_msg['data']:
                sLink = f'<a href="{tmp_msg["data"]["url"]}" target="_blank">{tmp_msg["data"]["file"]}</a>'
                tips += ('\n' + ybtext.msg_skip[0].format(sLink))
                asw = tips 
            else:
                asw = tips + '\n' + f'<img src="{tmp_msg["data"]["url"]}" class="needload" alt="{tmp_msg["data"]["file"]}" onload="imageLoaded(\'{tmp_msg["data"]["file"]}\')">'
        else:
            asw = tmp_msg
        return asw
    
    def image_api(self, mode: str, org='', ratio=0):
        def randomlist(orglst) -> list:
            lst = []
            start = 0
            end = len(orglst)
            for i in range(5, len(orglst)+1, 5):
                end = i
                lst = lst + random.sample(orglst[start:end], end - start)
                start = end
            if start < len(orglst):
                lst = lst + \
                    random.sample(orglst[start:len(orglst)], len(orglst)-start)
            return lst

        def check_contain_chinese(check_str):
            for ch in check_str:
                if u'\u4e00' <= ch <= u'\u9fff':
                    return True
            return False

        def input_to_tag(org, mode):  # return: tag, continue
            def merge_tags(tags1,  tags2):
                merge = []
                for it in tags1:
                    for new in tags2:
                        if it == new:
                            merge.insert(0, it)
                        elif new != '':
                            merge.append(it + ' ' + new)
                if len(merge) == 0:
                    merge = tags1
                return merge

            def get_tag(tar, mode):
                if tar == '':
                    return []
                if tar in self.map_tags:
                    if type(self.map_tags[tar]) is list:
                        return [self.random_str(self.map_tags[tar]), ]
                    elif type(self.map_tags[tar]) is dict:
                        return [self.random_dict(self.map_tags[tar]), ]
                    else:
                        return [self.map_tags[tar], ]
                elif tar in ybtext.map_tags_fuzzy:
                    if type(ybtext.map_tags_fuzzy[tar]) is list:
                        tag = self.random_str(ybtext.map_tags_fuzzy[tar])
                    elif type(ybtext.map_tags_fuzzy[tar]) is dict:
                        tag = self.random_dict(ybtext.map_tags_fuzzy[tar])
                    else:
                        tag = ybtext.map_tags_fuzzy[tar]
                elif not check_contain_chinese(tar):
                    tag = tar
                elif mode == 1:  # pingyin
                    tag = self.pinyin(tar)
                elif mode == 2:  # english ``
                    tag = self.translate_assign(
                        tar, '英', {},).lower().strip().replace(' ', '_')
                    tag = re.sub('^the_', '', tag)
                    tag = re.sub('[?？!！]', "", tag)
                tag = tag.lower()

                myurl = 'https://yande.re/tag.json?name=' + \
                    tag + '&order=count&commit=Search&limit=20'
                lib.log(f'{tar}-->{tag}')

                response_tag = self.proxy_get(myurl)
                tags = [tag, ]
                if response_tag.status_code == 200:
                    response_tag.encoding = response_tag.apparent_encoding
                    res_list = json.loads(response_tag.text)
                    ft_list = []
                    sub_list = []
                    tags = []
                    for ires in res_list:
                        #print(f'res:{ires} tar:{tag} equ: {ires["name"] == tag}')
                        if ires['name'] == tag:
                            tags.append(ires['name'])
                        elif ires['type'] in (0, 3, 4):
                            if tag in ires['name'].split('_'):
                                ft_list.append(ires)
                            else:
                                sub_list.append(ires)
                    if len(ft_list) + len(sub_list) > 0:
                        # 从1级候选名单中抽取最多5个tag
                        end = min(5 - len(tags), len(ft_list))
                        rd_res = random.sample(ft_list[0:end], end)
                        for one in rd_res:
                            tags.append(one['name'])
                        # 如果tags不满5个,从2级候选名单中抽取
                        end = min(5 - len(tags), len(sub_list))
                        rd_res = random.sample(sub_list[0:end], end)
                        for one in rd_res:
                            tags.append(one['name'])
                else:
                    lib.log("Get " + myurl + " Fail status:" +
                          str(response_tag.status_code))
                return tags
            ma = re.search('^(\\S+?)([新热]|(宽高比.+))图', org)
            if ma:
                tars = ma.group(1).split(',')
                tags = []
                repeat_set = set()
                for tar in tars:
                    if not tar in repeat_set:
                        new_tags = get_tag(tar, mode)
                        if len(tags) == 0:
                            tags = new_tags
                        elif len(new_tags) != 0:
                            tags = merge_tags(tags, new_tags)
                        repeat_set.add(tar)
                    if len(tags) > 10:
                        break
                return tags, (len(tags) > 0)
            else:
                return ["", ], True

        def save_picture(img_url, path):
            if not os.path.isfile(path):
                start_time = time.time()
                response2 = self.proxy_get_stream(img_url)
                if response2.status_code == 200:
                    with open(path, "wb") as f:
                        # f.write(response2.content)
                        for chunk in response2.iter_content(chunk_size=1024):
                            if chunk:
                                f.write(chunk)
                    use_time = round(time.time() - start_time, 2)
                    lib.log(f"Pic {path} Writed Use {use_time}s")
                else:
                    lib.log("Get " + img_url + " Fail status:" +
                          str(response2.status_code))
        black_list = {'himura_kiseki', 'uncompressed_file',
                      'ringeko-chan', 'renberry'}
        skip_list = {'pussy', 'penis', 'sex', 'nipples', }
        ban_list = {'ass', 'breasts', 'nopan', 'naked', }  # 'no_bra'
        relate = '图'
        org = org.replace(' ', '')
        ma = re.search('^(\\S+?)([新热]|(宽高比.+))图', org)
        if ma:
            relate = ma.group(1)

        if mode == 'yande':
            try:
                user = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.164 Safari/537.36',
                        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'}
                addr = 'https://yande.re/post.json?limit=200'
                myurl = None
                tags, goon = input_to_tag(org, 2)
                lib.log("tags:", tags)
                if goon:
                    for tag in tags:
                        node1 = time.time()
                        myurl = addr
                        if tag != "":
                            myurl = myurl + '&tags=' + tag

                        rsp = self.proxy_get(myurl)
                        res_list = json.loads(rsp.text)

                        node2 = time.time()
                        lib.log("Yande search use {}s".format(
                            round(node2-node1, 3)))
                        sample_res = randomlist(res_list)
                        for res in sample_res:
                            # 分解url
                            myurl = res['jpeg_url']
                            sampleurl = res['sample_url']
                            preurl = res['preview_url']
                            match = re.search('yande\.re%(\d+?)%', myurl)
                            filename = match.group(1)+".jpg"
                            # print("filename:"+filename)

                            tags = set(res['tags'].split())
                            rating = res['rating']
                            file_size = int(res['file_size'])

                            if not tags.isdisjoint(black_list):
                                continue
                            ifskip = not tags.isdisjoint(skip_list)
                            if ifskip:
                                continue  # 屏蔽色图
                            ban = (not tags.isdisjoint(ban_list)
                                   or rating == 'e') and (rating != 's')
                            delay = math.floor(
                                abs(time.time() - res['created_at'])/3600)

                            path = os.path.join(self.pic_path, filename)
                            path_s = os.path.join(
                                self.pic_path, "sample", filename)
                            path_p = os.path.join(
                                self.pic_path, "preview", filename)

                            #not os.path.isfile(path)
                            if not self.cur_send_user in self.oldimg_lst:
                                self.oldimg_lst[self.cur_send_user] = []

                            if not filename in self.oldimg_lst[self.cur_send_user]:
                                lib.log("Tags:{}\nDelay:{}h, Size:{}M, Rating:{}, Skip:{}, Ban:{}".format(
                                    tags, delay, round(file_size/(1024*1024), 2), rating, ifskip, ban))
                                ma = re.search(
                                    'i\d*\.pximg\.net.*\/(\d+?)(_p\d+)?\.\S+', res['source'])
                                if ma:
                                    res['source'] = "https://www.pixiv.net/artworks/" + \
                                        ma.group(1)
                                    #print( "new source",res['source'] )
                                node3 = time.time()
                                lib.log("Fitter E img use {}s".format(
                                    round(node3-node2, 3)))
                                largesize = (file_size > 5242880)
                                # 缓存图片
                                if not os.path.isfile(path) or (largesize and not os.path.isfile(path_s)):
                                    save_picture(myurl, path)
                                    if largesize:
                                        save_picture(sampleurl, path_s)
                                if not os.path.isfile(path_p):
                                    save_picture(preurl, path_p)
                                # 构造图片信息
                                tmp_msg = {'type': "image", 'data': {'file': filename, 'url': os.path.join(self.pic_path, filename),
                                                                     'source': res['source'], 'delay': delay, 'size': file_size, 'tags': ','.join(list(tags)[:20])}}
                                # self.lastimgfile = filename
                                if largesize:
                                    tmp_msg['data']['url'] = os.path.join(self.pic_path, "sample", filename)
                                    tmp_msg['data']['sample'] = True
                                if ifskip:
                                    tmp_msg['data']['skip'] = True
                                return tmp_msg, ban
                self.stopimg = True
                return ybtext.msg_notexists[2].format(relate), False
            except Exception as e:
                lib.log(f'yande error: {str(e)}')
                if re.search('Cannot connect to proxy', str(e)):
                    tmp_msg = ybtext.msg_bug[1]
                elif re.search('No wife', str(e)):
                    tmp_msg = ybtext.msg_bug[3]
                else:
                    tmp_msg = ybtext.msg_bug[0]
                    traceback.print_exc()
                if myurl != None:
                    lib.log("myurl:", myurl)
            return tmp_msg, False
        elif mode == 'yande_hot':
            try:
                user = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36',
                        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'}
                addr = 'https://yande.re/post.json?limit=100'
                myurl_img = None
                org = org.strip()
                tags, goon = input_to_tag(org, 2)
                lib.log("tags:", tags)
                if goon:
                    for tag in tags:
                        myurl = addr
                        if tag != "":
                            myurl = myurl + '&tags=' + tag

                        for i in range(1, 9):
                            node1 = time.time()
                            myurl_page = myurl + "&page=" + str(i)
                            response = self.proxy_get(myurl_page)
                            try:
                                res_list = json.loads(response.text)
                            except json.JSONDecodeError as je:
                                lib.log(
                                    f'JSONDecodeError:{repr(je)}\nText: {response.text}')
                                continue

                            node2 = time.time()
                            lib.log("Yande search use {}s".format(
                                round(node2-node1, 3)))
                            sample_res = res_list
                            if len(sample_res) == 0:
                                break
                            for res in sample_res:

                                tags = set(res['tags'].split())
                                rating = res['rating']
                                if not tags.isdisjoint(black_list):
                                    continue
                                ifskip = not tags.isdisjoint(skip_list)
                                ban = (not tags.isdisjoint(ban_list)
                                       or rating == 'e') and (rating != 's')
                                delay = math.floor(
                                    abs(time.time() - res['created_at'])/3600)
                                score = int(res['score'])
                                #doorsill = (-(delay-24)*(delay-24) + 576)/20 if delay<=24 else 30
                                doorsill = math.floor(
                                    20 * (1 - math.exp(-(delay+3)/8)) if delay < 24 else 20)
                       
                                if ratio > 0:
                                    width = int(res['width'])
                                    height = int(res['height'])
                                    wh = width/height
                                    if wh <= ratio - 0.3 or wh >= ratio + 0.3:
                                        continue
                                elif ifskip and score < doorsill * 3 or ban and score < doorsill * 1.5 or score < doorsill:
                                    continue

                                # 分解url
                                file_size = int(res['file_size'])
                                myurl_img = res['jpeg_url']
                                match = re.search(
                                    'yande\.re%(\d+?)%', myurl_img)
                                filename = match.group(1)+".jpg"
                                sampleurl = res['sample_url']
                                preurl = res['preview_url']

                                path = os.path.join(self.pic_path, filename)
                                path_s = os.path.join(
                                    self.pic_path, 'sample', filename)
                                path_p = os.path.join(self.pic_path, 'preview', filename)
                                if not self.cur_send_user in self.oldimg_lst:
                                    self.oldimg_lst[self.cur_send_user] = []

                                if not filename in self.oldimg_lst[self.cur_send_user]:
                                    lib.log("Tags:{}, Rating:{}, Skip:{}, Ban:{}\nDelay:{}h, Size:{}M, Score/Door:{}/{}".format(
                                        tags, rating, ifskip, ban, delay, round(file_size/(1024*1024), 2), score, doorsill,))
                                    node3 = time.time()
                                    lib.log("Fitter old img use {}s".format(
                                        round(node3-node2, 3)))
                                    largesize = (file_size > 5242880)
                                    ma = re.search(
                                        'i\d*\.pximg\.net.*\/(\d+?)(_p\d+)?\.\S+', res['source'])
                                    if ma:
                                        res['source'] = "https://www.pixiv.net/artworks/" + \
                                            ma.group(1)
                                    if not os.path.isfile(path) or (largesize and not os.path.isfile(path_s)):
                                        # 如果没有缓存,下载图片
                                        save_picture(myurl_img, path)
                                        if largesize:
                                            save_picture(sampleurl, path_s)
                                    if not os.path.isfile(path_p):
                                        save_picture(preurl, path_p)
                                    # 构造图片信息
                                    tmp_msg = {'type': "image", 'data': {'file': filename, 'url': os.path.join(self.pic_path, filename),
                                                                         'source': res['source'], 'delay': delay, 'size': file_size, 'tags': ','.join(list(tags)[:20])}}
                                    if largesize:
                                        tmp_msg['data']['url'] = os.path.join(self.pic_path, "sample", filename)
                                        tmp_msg['data']['sample'] = True
                                    #self.lastimgfile = filename
                                    if ifskip:
                                        tmp_msg['data']['skip'] = True
                                    return tmp_msg, ban
                self.stopimg = True
                return ybtext.msg_notexists[2].format(relate), False
            except Exception as e:
                lib.log(f'yande_hot error: {str(e)}', e.args[0])
                if re.search('Cannot connect to proxy', str(e)):
                    tmp_msg = ybtext.msg_bug[1]
                elif re.search('No wife', str(e)):
                    tmp_msg = ybtext.msg_bug[3]
                else:
                    tmp_msg = ybtext.msg_bug[0]
                    traceback.print_exc()
                if myurl_img != None:
                    lib.log("myurl_img:", myurl_img)
            return tmp_msg, False
        return "Error No Api", False
    def deleteimg(self, id, message = ''):
        send = str(id)
        filename = message.replace(' ', '')
        path = os.path.join(self.pic_path, filename) 
        path_s = os.path.join(self.pic_path, "sample", filename)
        path_p = os.path.join(self.pic_path, "preview", filename)
        if os.path.exists(path):
            os.remove(path)
            print(f'删除文件{path}')
        if os.path.exists(path_s):
            os.remove(path_s)
            print(f'删除文件{path_s}')
        if os.path.exists(path_p):
            os.remove(path_p)
            print(f'删除文件{path_p}')
        self.imgdb.delete(filename, send)
        if send in self.oldimg_lst and filename in self.oldimg_lst[send]:
            self.oldimg_lst[send].remove(filename)
        return ybtext.msg_delete[0]
    def proxy_get(self, url, ):
        user = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'}
        proxies = {'http': 'http://127.0.0.1:7890',
                   'https': 'http://127.0.0.1:7890'}
        yande_cookie = {'user_id': '55635', 'user_info': '55635%3B30%3B0'}
        sess = requests.Session()
        sess.keep_alive = False
        i = 0
        while i < 5:
            try:
                response = requests.get(
                    url, headers=user, proxies=proxies, cookies=yande_cookie, timeout=60)
                response.encoding = response.apparent_encoding
                return response
            except MemoryError as me:
                i += 5
                lib.log(f'proxy get error: MemoryError')
                raise MemoryError("HTTP Get Over Memory")
            except Exception as e:
                i += 1
                lib.log(f'proxy get error times {i}:\n{repr(e)}')
                time.sleep(0.2)
        raise Exception('Cannot connect to proxy')

    def proxy_get_stream(self, url, ):
        user = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'}
        proxies = {'http': 'http://127.0.0.1:7890',
                   'https': 'http://127.0.0.1:7890'}
        yande_cookie = {'user_id': '55635', 'user_info': '55635%3B30%3B0'}
        sess = requests.Session()
        sess.keep_alive = False
        i = 0
        while i < 5:
            try:
                response = requests.get(
                    url, headers=user, proxies=proxies, timeout=60, cookies=yande_cookie, stream=True)
                #response.encoding = response.apparent_encoding
                return response
            except MemoryError as me:
                i += 5
                lib.log(f'proxy get error: MemoryError')
                raise MemoryError("HTTP Get Over Memory")
            except Exception as e:
                i += 1
                lib.log(f'proxy get error times {i}:\n{repr(e)}')
        raise Exception('Cannot connect to proxy')
    
    chat_ai_time = {'0': 0}
    chat_lst = {}
    ###mode: 1:completions 2:chat
    def chat_gpt(self, org, id, mode = 2) -> str:
        def chat_lst2prompt(chat_lst):
            conversations = []
            for index in chat_lst:
                conversations.append(f"{index['role']}: {index['content']}")
            conversations.append(f"{ybtext.gpt_name}:")
            prompt = '\n'.join(conversations)
            return prompt
        target = id
        if target not in self.chat_ai_time:
            self.chat_ai_time[target] = 0
        if target not in self.chat_lst:
            self.chat_lst[target] = []
        dialogue_life = 600
        usr_name = 'user'
        asw = self.random_str(ybtext.gpt_connect_error)
        org = org.strip()
        user = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {openai.api_key}'}
        proxies = {'http': 'http://127.0.0.1:7890',
                   'https': 'http://127.0.0.1:7890'}
        date = time.strftime("%Y-%m-%d")

        if mode == 1:
            sys_msg = ybtext.gpt_sys_msg[1].format(date) + '\n'
            usr_name = str(id)
        elif mode ==2:
            sys_msg = [{'role': 'system', 'content': ybtext.gpt_sys_msg[0].format(date)}]

        if (time.time() - self.chat_ai_time[target] > dialogue_life) or re.search(ybtext.gpt_keyword[0], org): #清空对话缓存
            self.chat_lst[target] = []

        self.chat_lst[target].append({"role": usr_name, 'content': org})

        if mode == 1:
            self.chat_lst[target] = self.chat_lst[target][-14:]
            url = "https://api.openai.com/v1/completions"
            prompt = chat_lst2prompt(self.chat_lst[target])
            datas = {"model": "text-davinci-003", "prompt": sys_msg + prompt, "max_tokens": 512, "temperature": 0.8}
        elif mode == 2:
            self.chat_lst[target] = self.chat_lst[target][-20:]
            url = "https://api.openai.com/v1/chat/completions"
            datas = {"model": "gpt-3.5-turbo", "messages": sys_msg + self.chat_lst[target], "max_tokens": 512, "temperature": 0.8}

        lib.log(f"Now chat size: {len(self.chat_lst[target])}")

        try:
            node1 = time.time()
            response = requests.post(url, headers=user, proxies=proxies, timeout=60, json=datas)
            timecost = math.ceil(time.time() - node1)
            lib.log(f'ChatGPT Response in {timecost}s')
            if response.status_code != 200:
                lib.log("ChatGpt Api Error Response:",response)
                self.chat_lst[target].pop()
            else:
                if mode == 1:
                    gpt_msg = json.loads(response.text)["choices"][0]["text"]
                    self.chat_lst[target].append({"role": ybtext.gpt_name, "content": gpt_msg.strip()})
                elif mode == 2:
                    gpt_msg = json.loads(response.text)["choices"][0]["message"]["content"]
                    self.chat_lst[target].append({"role": "assistant", "content": gpt_msg.strip()})
                
                lib.log(f'Now Conversation Usage:{json.loads(response.text)["usage"]}')
                
                asw = gpt_msg.strip()
                if re.search(ybtext.gpt_keyword[0], org):
                    self.chat_lst[target] = []
        except Exception as e:
            lib.log(e)
            self.chat_lst[target].pop()
            if isinstance(e, socket.timeout):
                asw = self.random_str(ybtext.msg_timeout)
        if re.search(ybtext.gpt_keyword[1], org):
            self.chat_ai_time[target] = 0
        else:
            self.chat_ai_time[target] = time.time()
        return asw
    
    def deepseek_chat(self, org, id) -> str:
        target = id
        if target not in self.chat_ai_time:
            self.chat_ai_time[target] = 0
        if target not in self.chat_lst:
            self.chat_lst[target] = [] 
        usr_name = 'user'
        asw = self.random_str(ybtext.gpt_connect_error)
        org = org.strip()

        date = time.strftime("%Y-%m-%d")

        #systemconfig
        systemword = ybtext.gpt_sys_msg[0].format(date)
        dialogue_limit = 40
        dialogue_life = 600
        if 'chatgpt' in self.config:
            if 'tips' in self.config['chatgpt']:
                systemword = self.config['chatgpt']['tips'] + \
                    '.' + ybtext.gpt_sys_msg[1].format(date)
            if 'sizelimit' in self.config['chatgpt']:
                dialogue_limit = int(self.config['chatgpt']['sizelimit'])
            if 'timelimit' in self.config['chatgpt']:
                dialogue_life = int(self.config['chatgpt']['timelimit'])
        sys_msg = [{'role': 'system', 'content': systemword}]

        if (time.time() - self.chat_ai_time[target] > dialogue_life) or re.search(ybtext.gpt_keyword[0], org): #清空对话缓存
            self.chat_lst[target] = []

        self.chat_lst[target].append({"role": usr_name, 'content': org})


        self.chat_lst[target] = self.chat_lst[target][-dialogue_limit:]

        url = "https://api.deepseek.com/chat/completions"
        chatdata = json.dumps({
            "messages": sys_msg + self.chat_lst[target],
            "model": "deepseek-chat",
            "frequency_penalty": 0,
            "max_tokens": 1024,
            "response_format": {
                "type": "text"
            },
            "stop": None,
            "stream": False,
            "temperature": 1.3,
            })
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {openai.api_key}'
        }

        lib.log(f"Now chat size: {len(self.chat_lst[target])}")

        try:
            node1 = time.time()
            response = requests.request("POST", url, headers=headers, data=chatdata)
            timecost = math.ceil(time.time() - node1)
            lib.log(f'DeepSeek Response in {timecost}s')

            res = json.loads(response.text)
            ds_msg = res['choices'][0]['message']['content']
            self.chat_lst[target].append({"role": "assistant", "content": ds_msg.strip()})
                
            lib.log(f'Now Conversation Usage:{res["usage"]["total_tokens"]}')
                
            asw = ds_msg.strip()
            if re.search(ybtext.gpt_keyword[0], org):
                self.chat_lst[target] = []
        except Exception as e:
            lib.log(e)
            self.chat_lst[target].pop()
            if isinstance(e, socket.timeout):
                asw = self.random_str(ybtext.msg_timeout)
        if re.search(ybtext.gpt_keyword[1], org):
            self.chat_ai_time[target] = 0
        else:
            self.chat_ai_time[target] = time.time()
        return asw
    
    def TodayInHis(self):
        today = time.strftime('%m%d')
        return self.InHis(today)
    
    def InHis(self, mmdd:str):
        month = mmdd.strip()[:2]
        addr = f'https://baike.baidu.com/cms/home/eventsOnHistory/{month}.json'
        #print(addr)
        user = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'}
        try:
            f = requests.get(addr, headers=user, timeout=60)
            if f.status_code == 200: 
                res = json.loads(f.text)
                lst_event = res[month][mmdd]
                set_fes = set()
                lst_his = []
                for event in lst_event:
                    year = event['year']
                    festival = event['festival']
                    title = event['title']
                    title = re.sub("</?a.*?>", "", title)
                    t = event['type']
                    if t not in {'birth', 'death'}:
                        lst_his.append(f'{year}: {title}')
                    if festival and festival != "":
                        set_fes.add(festival)
                lst_his.reverse()
                rep = ""
                if len(set_fes)>0:
                    rep = ybtext.msg_history[0].format(",".join(set_fes))
                rep += "\n".join(lst_his)
                return rep
            else:
                return ybtext.msg_history[1]
        except Exception as e:
            traceback.print_exc()
            return ybtext.msg_history[1]
        
    def versify(self, org) -> str:
        asw = ""
        org = org.strip()
        myurl = "http://api.tianapi.com/txapi/cangtoushi/index"
        key = "66faeca0e430e6febbe4790551188a10"
        ma = re.match("藏([头尾中增减])诗[:：](\\S+)", org)
        modedict = {"头": 1, "尾": 2, "中": 3, "增": 4, "减": 5}
        versify_type = 1
        if ma:
            versify_type = modedict[ma.group(1)]
        else:
            return ybtext.msg_notfind[2]
        words = ma.group(2)
        myurl = myurl + "?key=" + key + "&len=1" + "&word=" + \
            urllib.parse.quote(words, 'uft-8') + "&type=" + str(versify_type)
        try:
            f = urllib.request.urlopen(myurl, timeout=8)

            result_all = f.read()
            result = json.loads(result_all)
            if result['code'] != 200:
                return ybtext.msg_fail[2]
            for list in result['newslist']:
                if asw == "":
                    asw = asw + list['list']
                else:
                    asw = asw + "\n" + list['list']
        except Exception as e:
            traceback.print_exc()
            print("myurl:", myurl)
            if isinstance(e, socket.timeout):
                asw = self.random_str(ybtext.msg_timeout)
        return asw
    
    def image_map(self, key: str, value: str):
        key = key.strip()
        value = value.strip().lower()
        if key in self.map_tags:
            new_v = []
            v = self.map_tags[key]
            if type(v) == str:
                new_v.append(v)
            elif type(v) == list:
                new_v = v
            else:
                print("add_tag map_tag format error")
                return 'add_tag map_tag format error'
            if value not in new_v:
                new_v.append(value)
                self.map_tags[key] = new_v
        else:
            self.map_tags[key] = value
        json.dump(self.map_tags, open('tags.json', 'w', encoding='utf-8'))
        return ""
    def cast_as_eval(self, org) -> str:
        code = org.strip()
        code = code.replace('^', '**')
        import html
        code = html.unescape(code)
        print(time.strftime("[%Y-%m-%d %H:%M:%S]",
              time.localtime()), "Cast as eval:", code)
        answer = ''
        try:
            answer = str(eval(code))
            if answer == '':
                answer = 'success'
        except Exception as e:
            traceback.print_exc()
            answer = "执行失败"
        return answer
    def get_tophub(self) -> str:
        limit = self.config['tophup_limit'] or 20

        head = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36',
                'accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'}
        url = "https://www.baidu.com"

        asw = ybtext.msg_notfind[2]
        try:
            res = requests.request('GET', url, headers=head)
            htmltext = res.text 
            
            # with open('temphtml.txt', 'wb') as ff:
            #     ff.write(res.content)
            # print(htmltext)
            matchs = re.findall('"card_title":.*?\}', htmltext, re.DOTALL)
            if len(matchs) > 0:
                asw = ""
                for strTop in matchs:
                    strTop = '{' + strTop
                    # print(strTop)
                    try:
                        jTop = json.loads(strTop)
                        if (int(jTop["index"]) <= limit):
                            asw += f'{jTop["index"]}.<a href={urllib.parse.unquote(jTop["linkurl"])} target="_blank">{jTop["card_title"]}</a>' + '\n'
                    except Exception as e:
                        if isinstance(e, json.decoder.JSONDecodeError):
                            next
                        else:
                            print(type(e), e)
        except Exception as e:
            if isinstance(e, socket.timeout):
                print("socket timeout")
            else:
                print(type(e), e)
        return asw
    def inversion(self, org:str) -> str:
        return org[::-1]
        
if __name__ == '__main__':
    qm = Message({})
