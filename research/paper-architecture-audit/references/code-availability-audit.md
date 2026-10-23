# 代码可用性核查

审完论文正文与附录之后走这一步。结论决定主人能不能立刻开工，也决定下一封信该索要什么。

## 四条证据链，按顺序走

1. **附录里的产物路径**。出现 `results/<something>/`、`scripts/`、实验配置文件名，说明组内有工程仓库。这不算证据证明公开，但证明存在。
2. **作者主页的链接栏**。个人主页常把 GitHub handle 写成一排小链接；抓 HTML 比读正文可靠。
3. **项目页的 Code 链接**。论文项目页（`*.github.io/<project>/`）通常在标题下放 `Paper | Code | arXiv`。**markdown 抽取常把行内链接剥掉**，所以抓 href：
   ```bash
   curl -sL <project-page> | grep -o -E 'href="[^"]+"' | grep -i -E 'github|code|arxiv' | sort -u
   ```
4. **组织仓库全表**。这一张表信息量最大：能看出开源文化、相关方向的在研项目、以及哪一篇缺代码。

## 命令

```bash
# 仓库元信息
curl -s https://api.github.com/repos/OWNER/REPO | python3 -c "import sys,json;d=json.load(sys.stdin);[print(k,d.get(k)) for k in ['full_name','description','language','stargazers_count','created_at','updated_at','license']]"

# 组织下全部仓库
curl -s "https://api.github.com/orgs/ORG/repos?per_page=100" | python3 -c "import sys,json;[print(r['name'],r.get('language'),r['stargazers_count'],r['updated_at'][:10],(r['description'] or '')[:60]) for r in json.load(sys.stdin)]"

# 个人账号下的仓库（判断作者的发布习惯）
curl -s "https://api.github.com/users/HANDLE/repos?per_page=100&sort=updated"

# 读 README（最容易读到「已被新仓库取代」的地方）
curl -sL https://raw.githubusercontent.com/OWNER/REPO/main/README.md | head -60

# 按关键词搜仓库
curl -s "https://api.github.com/search/repositories?q=KEYWORDS"
```

**仓库搜索不需要认证，代码搜索需要。** 没做代码搜索就不要声称「搜过代码」。

## 读结果的五条判断

- **个人账号下每篇论文都有复现代码、单独某一篇没有** → 大概率是还没整理，不是不愿给。索要的风险很低，而且是顺着他们自己的习惯开口。
- **README 顶部的 "Update: we moved forward / subsumes this one"** → 论文时代的仓库已过期，读新的那个，别照着旧代码复现。
- **同组组织下有同方向的在研仓库** → 主人要做的方向可能已经有人在做。先看这些仓库的最近更新时间，再决定要不要往那个方向写。
- **仓库里既有求解器又有世界模型时，先读求解器那层** → 那是能接自己东西的接口层；世界模型是对方任务特有的，未必可复用。
- **搜遍关键词为 0、且作者账号里也没有** → 结论写「在我的检索范围内未找到公开仓库」，不写「不存在」。私有、还没整理、放在未公开的组内 Git 都有可能。

## 写进交付物的一句话

> 论文 X 的代码未公开；其附录提到的 `results/xxx/` 说明组内有工程仓库。论文 Y 的代码在 `ORG/repo`，但 README 已指向 `ORG/repo-new`，应读后者。

这条比论文的任何技术细节都更影响下一步动作，所以放在纪要的资产表里，别埋在正文。
