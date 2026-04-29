import os

import shutil
import random

import tqdm   


path = r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\experiment\E1\metadata.all.txt"

train_cnt = 0
t_bonafide_cnt = 0
t_spoof_cnt = 0
eval_cnt = 0
e_bonafide_cnt = 0
e_spoof_cnt = 0
dev_cnt = 0
d_bonafide_cnt = 0
d_spoof_cnt = 0
else_cnt = 0
        
with open(path, 'r', encoding='utf-8') as f:
    for line in f:
        type = line.strip().split()[1][3]
        if type == "T":
            train_cnt += 1
            sb = line.strip().split()[4]
            if sb == "bonafide":
                t_bonafide_cnt += 1
            elif sb == "spoof":
                t_spoof_cnt += 1
        elif type == "E":
            eval_cnt += 1
            sb = line.strip().split()[4]
            if sb == "bonafide":
                e_bonafide_cnt += 1
            elif sb == "spoof":
                e_spoof_cnt += 1
        elif type == "D":
            dev_cnt += 1
            sb = line.strip().split()[4]
            if sb == "bonafide":
                d_bonafide_cnt += 1
            elif sb == "spoof":
                d_spoof_cnt += 1
        else:
            else_cnt += 1
            
            
total_cnt = train_cnt + eval_cnt + dev_cnt + else_cnt
total_bonafide_cnt = t_bonafide_cnt + e_bonafide_cnt + d_bonafide_cnt
total_spoof_cnt = t_spoof_cnt + e_spoof_cnt + d_spoof_cnt
print(f"train_cnt\t{train_cnt}\tbonafide:\t{t_bonafide_cnt}({round(t_bonafide_cnt/train_cnt*100, 2)}%)\tspoof:\t{t_spoof_cnt}({round(t_spoof_cnt/train_cnt*100, 2)}%)")
print(f"dev_cnt\t\t{dev_cnt}\tbonafide:\t{d_bonafide_cnt}({round(d_bonafide_cnt/dev_cnt*100, 2)}%)\tspoof:\t{d_spoof_cnt}({round(d_spoof_cnt/dev_cnt*100, 2)}%)")
print(f"eval_cnt\t{eval_cnt}\tbonafide:\t{e_bonafide_cnt}({round(e_bonafide_cnt/eval_cnt*100, 2)}%)\tspoof:\t{e_spoof_cnt}")
# print(f"else_cnt\t{else_cnt}")
print(f"total\t\t{total_cnt}\tbonafide:\t{total_bonafide_cnt}({round(total_bonafide_cnt/total_cnt*100, 2)}%)\tspoof:\t{total_spoof_cnt}({round(total_spoof_cnt/total_cnt*100, 2)}%)")