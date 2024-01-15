#msg_deal.py
import urllib
from urllib import request, error
import time
import re
import json
import math
import socket
import os

import mlib as lib
import ybtext

class Message:
    date_jieqi = {}

    def __init__(self):
        if os.path.exists('jieqi.json'):
            self.date_jieqi = json.load(open('jieqi.json'))
        else:
            json.dump(self.date_jieqi, open('jieqi.json', 'w'))

    def deal(self, msg, sid = 0) -> str:
        replay = "这是一个默认回复。"
        if re.match('^干支[:：]?(.*)', msg):
            mt = re.match('干支[:：]?(.*)', msg)
            org = mt.group(1)
            replay = self.ganzhi(org)[0]
        elif re.match('下个吉时', msg):
            replay = self.nextqmds()
        return replay

    def getjieqi(self, date_q) -> str:
        ct = 0
        idate = date_q
        jieqi = ""
        myurl = "http://api.tianapi.com/txapi/lunar/index"
        key = "66faeca0e430e6febbe4790551188a10"
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
        key = "66faeca0e430e6febbe4790551188a10"
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
            return ybtext.msg_illegal[5]
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
                asw = asw + str(ndate) + '\n'
            time.sleep(1)
        if asw == '':
            return ybtext.msg_notfind[2]
        else:
            return asw
if __name__ == '__main__':
    qm = Message()
    asw, _, _ = qm.ganzhi("-1")
    #asw = qm.nextqmds()
    print(asw)
