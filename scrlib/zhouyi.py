import random
import time

try:
    import mlib as mlib
except ImportError:
    import scrlib.mlib as mlib

map_yaobian = {0:"无变爻, 以本卦卦辞为根据",
               1:"一爻变化, 以{}爻辞为根据",
               2:"二爻变化, 以{}爻辞为根据,以上爻为主",
               3:"三爻变化, 以本卦变卦卦辞为根据",
               4:"四爻变化, 以变卦的{}爻为根据,以下爻为主",
               5:"五爻变化, 以变卦的{}爻为根据",
               6:"六爻变化, 以变卦卦辞为根据,乾坤卦以用九/用六为根据"}

map_bagua = {0:'☷', 1:'☳', 2:'☵', 3:'☱', 4:'☶', 5:'☲', 6:'☴', 7:'☰'}


map_xiang = {63: '乾', 62: '姤', 61: '同人', 60: '遁',
             59: '履', 58: '讼', 57: '无妄', 56: '否', 55: '小畜', 54: '巽', 53: '家人', 52: '渐', 51: '中孚', 50: '涣',
             49: '益', 48: '观', 47: '大有', 46: '鼎', 45: '离', 44: '旅', 43: '睽', 42: '未济', 41: '噬嗑', 40: '晋',
             39: '大畜', 38: '蛊', 37: '賁', 36: '艮', 35: '损', 34: '蒙', 33: '颐', 32: '剥', 31: '夬', 30: '大过',
             29: '革', 28: '咸', 27: '兑', 26: '困', 25: '随', 24: '萃', 23: '需', 22: '井', 21: '既济', 20: '蹇',
             19: '节', 18: '坎', 17: '屯', 16: '比', 15: '大壮', 14: '恒', 13: '丰', 12: '小过', 11: '归妹', 10: '解',
             9: '震', 8: '豫', 7: '泰', 6: '升', 5: '明夷', 4: '谦', 3: '临', 2: '师', 1: '复', 0: '坤'}
map_menu = {63: 1, 62: 44, 61: 13, 60: 33,
            59: 10, 58: 6, 57: 25, 56: 12, 55: 9, 54: 57, 53: 37, 52: 53, 51: 61, 50: 59,
            49: 42, 48: 20, 47: 14, 46: 50, 45: 30, 44: 56, 43: 38, 42: 64, 41: 21, 40: 35,
            39: 26, 38: 18, 37: 22, 36: 52, 35: 41, 34: 4, 33: 27, 32: 23, 31: 43, 30: 28,
            29: 49, 28: 31, 27: 58, 26: 47, 25: 17, 24: 45, 23: 5, 22: 48, 21: 63, 20: 39,
            19: 60, 18: 29, 17: 3, 16: 8, 15: 34, 14: 32, 13: 55, 12: 62, 11: 54, 10: 40,
            9: 51, 8: 16, 7: 11, 6: 46, 5: 36, 4: 15, 3: 19, 2: 7, 1: 24, 0: 2}

def yibian(shicao: int) -> int:
    # 1
    d1 = round(random.gauss(shicao / 2, shicao / 6))
    if d1 < 1:
        d1 = 1
    elif d1 >= shicao:
        d1 = shicao - 1
    d2 = shicao - d1
    # mlib.log(f"1ying: d1:{d1}, d2:{d2}")
    # 2
    gua = random.randint(1, shicao)
    if gua > d1:
        d2 -= 1
    else:
        d1 -= 1
    # mlib.log(f"2ying: d1:{d1}, d2:{d2}")
    # 3,4
    yu1 = d1 % 4
    yu1 = 4 if (yu1 == 0) else yu1
    if d1 >= yu1:#防止d1为0的情况
        d1 -= yu1
    yu2 = d2 % 4
    yu2 = 4 if (yu2 == 0) else yu2
    if d2 >= yu2:
        d2 -= yu2
    # mlib.log(f"4ying: d1:{d1}, d2:{d2}")
    return d1 + d2

def yiyao() -> int:
    shicao = 50
    shicao = shicao - 1
    for i in range(3):
        shicao = yibian(shicao)
        # mlib.log(f"bian-{i+1}:{shicao}")
    res = int(shicao / 4)
    return res

def yigua(seed = '') -> int:
    
    random.seed(seed)

    yao_num = []
    bengua = {}
    biangua = {}
    bian_set = set()
    for i in range(6):
        yao_num.append(yiyao())
        if yao_num[i] == 9:
            bengua[i] = 1
            biangua[i] = 0
            bian_set.add(i+1)
        elif yao_num[i] == 8:
            bengua[i] = 0
            biangua[i] = 0
        elif yao_num[i] == 7:
            bengua[i] = 1
            biangua[i] = 1
        elif yao_num[i] == 6:
            bengua[i] = 0
            biangua[i] = 1
            bian_set.add(i+1)
        else:
            mlib.log(f"Error yao num:{yao_num[i]}")
            break

    xia_i = bengua[0] + bengua[1] * 2 + bengua[2] * 4
    shang_i = bengua[3] + bengua[4] * 2 + bengua[5] * 4
    xiang = xia_i + shang_i * 8
    bian_xia_i = biangua[0] + biangua[1] * 2 + biangua[2] * 4
    bian_shang_i = biangua[3] + biangua[4] * 2 + biangua[5] * 4
    bian_xiang = bian_xia_i + bian_shang_i * 8
    sRes = ''
    sRes += f'本卦: {map_bagua[shang_i]} {map_bagua[xia_i]} , {map_xiang.get(xiang, " ")}卦第{map_menu.get(xiang, 0)}\n'
    sRes += f'变卦: {map_bagua[bian_shang_i]} {map_bagua[bian_xia_i]} , {map_xiang.get(bian_xiang, " ")}卦第{map_menu.get(bian_xiang, 0)}\n'

    num_bian = len(bian_set)
    sRes += f'{num_bian}爻变化: {bian_set}\n'
    if num_bian <= 3:
        sRes += map_yaobian[num_bian].format(bian_set) + '\n'
    else:
        yu_set = {1, 2, 3, 4, 5, 6} - bian_set
        sRes += map_yaobian[num_bian].format(yu_set) + '\n'
    return sRes
    

    
def testyao():
    rec = {6:0,7:0,8:0,9:0}
    times = 200000
    for i in range(times):
        yao = yiyao()
        rec[yao] += 1
    mlib.log(f"record:{rec}, 6+8:{rec[6]+rec[8]}, 7+9:{rec[7]+rec[9]}")
    per = {}
    for i, v in rec.items():
        per[i] = round(v * 100 / times, 2)
    mlib.log(f"percent:{per}, 6+8:{per[6]+per[8]:.2f}%, 7+9:{per[7]+per[9]:.2f}%")

if __name__ == "__main__":
    random.seed(str(time.time()))
    print(yigua())

