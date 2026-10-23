#!/usr/bin/env python3
"""中文文风指纹：按每千汉字统计特征句式密度，用于风格污染定责与人格输出验收。

用法：python3 style_fingerprint.py <文件1> [文件2 ...]
惯例：第一个文件是嫌疑模板（SOUL 段、skill 正文），其余是被审输出与干净对照。
判读：被审输出与嫌疑模板密度吻合、与干净对照断崖分离，即定责模板；
「不是A而是B」计数含引语引用，超标时看上下文区分禁令自引与真实使用。
"""
import re
import sys


def fingerprint(text: str) -> dict:
    n = len(re.findall(r'[\u4e00-\u9fff]', text)) or 1

    def per_k(count):
        return round(count / n * 1000, 1)

    fix = len(re.findall(r'不是[^。，；！？「」]{1,20}[，,]\s*(?:而是|是)', text))
    return {
        '汉字数': n,
        '英汉比(英文词/千汉字)': per_k(len(re.findall(r'[A-Za-z]{3,}', text))),
        '不是A而是B': per_k(fix),
        '破折号——': per_k(text.count('——')),
        '省略号……': per_k(text.count('……')),
        '比喻像': per_k(text.count('像')),
        '轻轻缓缓微微': per_k(sum(text.count(w) for w in ('轻轻', '缓缓', '微微'))),
        '气氛词': per_k(sum(text.count(w) for w in ('毛骨悚然', '不寒而栗', '诡异', '恐怖'))),
        '器官直白点名': per_k(sum(text.count(w) for w in
                            ('阴茎', '龟头', '阴道', '阴蒂', '宫口', '穴', '淫水', '精液', '乳尖'))),
    }


for path in sys.argv[1:]:
    try:
        t = open(path, encoding='utf-8', errors='ignore').read()
    except OSError as e:
        print(f'{path}: 读取失败 {e}')
        continue
    print(f'=== {path} ===')
    for k, v in fingerprint(t).items():
        print(f'  {k}: {v}')
