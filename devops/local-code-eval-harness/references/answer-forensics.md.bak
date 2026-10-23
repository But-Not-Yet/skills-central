# 自由作答对比：抽取、真值、取证、风格 — 可复用配方

配合 SKILL.md §11 使用。所有片段均实测可用（纯标准库，无需 scipy/numpy）。

---

## 1. 从终端日志里抽出每题正文

**坑先记下：** 多份模型记录长得很像，而且**命令回显里本身就含 `== ANSWER ==` 这个标记字符串**（jq 过滤器里写着它），所以按标记切块会把回显切成正文块；按“最近锚点”反查也会错位。

**可靠做法：只留大块，再按内容特征分类。**

```python
import re, os, glob, json
RULES = [("Q1", r"t_{n-1}|非中心|尺度不变|t 统计量"),
         ("Q2", r"相对风险|NNT|RR=|置信区间"),
         ("Q3", r"连接池|acquired_duration|等待线程"),
         ("Q4", r"政体|选举民主制|寡头"),
         ("Q5", r"dedup|短路|set\.add")]
per = {}
for f in sorted(glob.glob(D + "/0*.txt")):
    t = open(f, encoding="utf-8", errors="replace").read()
    for b in re.split(r'=+ ANSWER =+', t):
        b = b.split("========== META ==========")[0]
        if len(b) < 400:            # 回显块都是几十字符，一刀切掉
            continue
        for tag, pat in RULES:
            if re.search(pat, b):
                if tag not in per or len(b) > len(per[tag]):
                    per[tag] = b
                break
```

**抽完必须抽查首句**：打印每题前 90 字人工看一眼，确认归属没串。小样本抽查比任何正则都可靠。

---

## 2. 先造标准答案（两法起步）

### 2.1 正则化不完全 beta 与 t 分布

```python
def betacf(a, b, x):
    MI, EPS, FP = 300, 3e-15, 1e-300
    qab, qap, qam = a+b, a+1, a-1
    c = 1.0; d = 1 - qab*x/qap
    if abs(d) < FP: d = FP
    d = 1/d; h = d
    for m in range(1, MI+1):
        m2 = 2*m
        aa = m*(b-m)*x/((qam+m2)*(a+m2)); d = 1+aa*d
        if abs(d) < FP: d = FP
        c = 1+aa/c
        if abs(c) < FP: c = FP
        d = 1/d; h *= d*c
        aa = -(a+m)*(qab+m)*x/((a+m2)*(qap+m2)); d = 1+aa*d
        if abs(d) < FP: d = FP
        c = 1+aa/c
        if abs(c) < FP: c = FP
        d = 1/d; de = d*c; h *= de
        if abs(de-1) < EPS: break
    return h

def betai(a, b, x):
    if x <= 0: return 0.0
    if x >= 1: return 1.0
    bt = math.exp(math.lgamma(a+b)-math.lgamma(a)-math.lgamma(b)
                  + a*math.log(x) + b*math.log(1-x))
    return bt*betacf(a,b,x)/a if x < (a+1)/(a+b+2) else 1-bt*betacf(b,a,1-x)/b

def t_cdf(t, nu):
    p = 0.5*betai(nu/2, 0.5, nu/(nu+t*t))
    return 1-p if t > 0 else p

def critv(alpha, nu):          # 双侧临界值
    lo, hi = 0.0, 20.0
    for _ in range(150):
        mid = (lo+hi)/2
        if t_cdf(mid, nu) < 1-alpha/2: lo = mid
        else: hi = mid
    return (lo+hi)/2
```

**独立交叉核验**：t 密度直接 Simpson 积分（`f(t)=Γ((ν+1)/2)/(√(νπ)Γ(ν/2))·(1+t²/ν)^(-(ν+1)/2)`）。两法必须一致。

### 2.2 非中心 t（功效计算的正解）

没有闭式解。最稳的做法是**对 χ² 混合分布数值积分**：
`P(T ≤ x) = E_V[Φ(x√(V/ν) − δ)]`，其中 `V ~ χ²_ν`。

```python
def nc_cdf(x, nu, d, N=200000):
    a = nu/2.0; lg = math.lgamma(a) + a*math.log(2.0)
    hi = nu + 12*math.sqrt(2*nu); h = hi/N; s = 0.0
    for i in range(N+1):
        v = i*h
        fv = 0.0 if v <= 0 else math.exp((a-1)*math.log(v) - v/2 - lg)
        c = 0.5*(1 + math.erf((x*math.sqrt(v/nu) - d)/math.sqrt(2)))
        s += (1 if i in (0, N) else (4 if i % 2 else 2))*c*fv
    return s*h/3

def power(kind, n, d, alpha=0.05):
    nu = n-1 if kind == "one" else 2*n-2
    delta = d*math.sqrt(n) if kind == "one" else d*math.sqrt(n/2)
    c = critv(alpha, nu)
    return 1 - (nc_cdf(c, nu, delta) - nc_cdf(-c, nu, delta))
```

**蒙特卡洛是第二把尺**（十分钟写，永远可信）：

```python
def power_mc(n, mu, sigma, nu, crit, N=400000):
    random.seed(7); hits = 0
    d = math.sqrt(n)*mu/sigma
    for _ in range(N):
        z = random.gauss(d, 1.0)
        v = sum(random.gauss(0,1)**2 for _ in range(nu))
        if abs(z/math.sqrt(v/nu)) > crit: hits += 1
    return hits/N
```

**理解错一个参数就会得到另一个配置的表值。** 单样本 `δ = d√n`，双样本每组 n `δ = d√(n/2)`，df 分别为 `n−1` 与 `2n−2`——这三个数必须分开算。常见表值很容易张冠李戴。

### 2.3 四格表（比例差）

```python
# a,b = 组1 事件/非事件; c,d = 组2
chi2  = N*(a*d-b*c)**2/((a+b)*(c+d)*(a+c)*(b+d))            # 未校正
chi2y = N*(abs(a*d-b*c)-N/2)**2/((a+b)*(c+d)*(a+c)*(b+d))   # Yates
p_chi = 1 - math.erf(math.sqrt(chi2/2))                       # df=1
pp = (a+c)/N; se = math.sqrt(pp*(1-pp)*(1/n1+1/n2))
Z = (a/n1 - c/n2)/se;  p_z = 2*(1 - 0.5*(1+math.erf(abs(Z)/math.sqrt(2))))
RR = (a/n1)/(c/n2)
se_ln = math.sqrt(1/a - 1/n1 + 1/c - 1/n2)                    # Katz
CI = (math.exp(math.log(RR)-1.96*se_ln), math.exp(math.log(RR)+1.96*se_ln))
# Fisher 双侧：超几何全枚举，累加 p ≤ p_obs 的项（用 lgamma 取 log 组合数）
```

---

## 3. 归属取证：grep 原件，不凭记忆

要判定某个可疑数字/说法属于哪一份记录：**在该文件里数它出现了几次，再打印上下文**。

```python
for s in ["0.3398", "G*Power", "power.t.test", "0.8286"]:
    for k, txt in files.items():
        n = txt.lower().count(s.lower())
        if n: print(f"{s:<14} {k:<9} x{n}")
    for m in re.finditer(re.escape(s), txt, re.I):
        i = m.start()
        print("   …", re.sub(r'\s+', ' ', txt[max(0,i-230):i+150]))
```

**为什么必须这样做：** 三份记录结构、用词、格式高度相似，凭印象归属会错——本类任务中我们已经因为不 grep 而两次把错误归给了错的模型。

---

## 4. 引用审计清单

逐条问**两个**问题，答案分三档：

| 问题 | 不成立时 |
|---|---|
| 这个作者/书**存不存在**？ | **伪造**——最重的一档 |
| 它**真的讲这个主题**吗？ | **挂名松**——书真但引不切题，记但不与伪造混算 |

- 存在 + 对题 → ✅
- 存在 + 跑题 → ⚠️ 挂名松
- 不存在 → ❌ 伪造

**实例类型（供识别）：** 把同领域的另一个学科的知名人名当成政治学/相应领域作者；
把 A 学者的招牌概念挂到 B 学者名下；引一个真实存在的书名去支撑它根本没讨论的定义。

**搜索关键词配方：** `<人名> <领域> <概念>`、`<书名> <年份> <出版社>`、
`"<逐字短语>" <疑似原始作者>`。

---

## 5. 思考段→答案一致性

```python
# 把答案里的关键数字逐个回到该份记录的思考段找
t = open(f, encoding="utf-8", errors="replace").read()
for num in ["0.45", "0.15", "0.0298"]:
    print(num, t.count(num))
```

**判据：答案里出现、而思考段零出现的数字 = 凭空填入。** 这是独立于一档错误（算错）：
算错尚有推理可追，凭空填入连推理都不存在。

---

## 6. 行文风格量化（中文）

```python
def style(txt):
    t = re.sub(r'```.*?```', '', txt, flags=re.S)     # 先剔代码块
    sents = [s for s in re.split(r'[。！？\n]', t) if len(s.strip()) > 4]
    lens = [len(s) for s in sents]
    return {
        "平均句长": round(sum(lens)/len(lens), 1),
        "最长句":   max(lens),
        "对…进行":  len(re.findall(r'对[^。，]{0,12}进行', t)),
        "的密度%":  round(t.count("的")/max(1,len(t))*100, 2),
        "英文夹带": len(re.findall(r'[A-Za-z]{4,}', t)),
    }
```

**读数：** 平均句长越长、`对…进行` 越多 → 越欧化；`的` 密度过高 → 名词堆叠；
英文夹带高 → 中英夹杂（别把未译术语当优点）。代码块必须剔除，否则数字全被示例带偏。

---

## 7. 给出反解结论的写法

找到“不可能的数值”后，报告里要同时给三件事，缺一不可：

1. **真值**及其两种算法；
2. **反解**：什么配置才会给出那个数，与本题参数差多少；
3. **模型声称的命令行真跑一遍**的值。

只写“它算错了”会被追问；三项全写，结论才立得住。
