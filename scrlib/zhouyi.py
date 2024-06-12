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


map_xiang = {63: '乾', 61: '同人', 60: '遁',
             59: '履', 58: '讼', 57: '无妄', 56: '否', 55: '小畜', 53: '家人',
             48: '观', 47: '大有', 45: '离', 43: '睽', 41: '噬嗑', 40: '晋',
             39: '大畜', 38: '蛊', 37: '賁', 34: '蒙', 33: '颐', 32: '剥', 30: '大过',
             28: '咸', 25: '随', 23: '需', 20: '蹇', 
             18: '坎', 17: '屯', 16: '比', 15: '大壮', 14: '恒', 10: '解',
             8: '豫', 7: '泰', 5: '明夷', 4: '谦', 3: '临', 2: '师', 1: '复', 0: '坤'}
map_menu = {63: 1, 61: 13, 60: 33, 
            59: 10, 58: 6, 57: 25, 56: 12, 55: 9, 53: 36,
            48: 20, 47: 14, 45: 30, 43: 38, 41: 21, 40: 35,
            39: 26, 38: 18, 37: 22, 34: 4, 33: 27, 32: 23, 30: 28,
            28: 31, 25: 17, 23: 5, 20: 39, 
            18: 29, 17: 3, 16: 8, 15: 34, 14: 32, 10: 40,
            8: 16, 7: 11, 5: 36, 4: 15, 3: 19, 2: 7, 1: 24, 0: 2}

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

def yigua() -> int:
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
    mlib.log(f'本卦: {map_bagua[shang_i]} {map_bagua[xia_i]}, {map_xiang.get(xiang, " ")}卦第{map_menu.get(xiang, 0)}')
    mlib.log(f'变卦: {map_bagua[bian_shang_i]} {map_bagua[bian_xia_i]}, {map_xiang.get(bian_xiang, " ")}卦第{map_menu.get(bian_xiang, 0)}')

    num_bian = len(bian_set)
    mlib.log(f'{num_bian}爻变化: {bian_set}')
    if num_bian <= 3:
        mlib.log(map_yaobian[num_bian].format(bian_set))
    else:
        yu_set = {1, 2, 3, 4, 5, 6} - bian_set
        mlib.log(map_yaobian[num_bian].format(yu_set))
    

    
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
    yigua()






