/* ══════════════════════════════════════════════════════════════════
   交互演示 · 全局进度数据  v1  2026-09-23
   ─────────────────────────────────────────────────────────────────
   ★ 这是"我在全局哪一格"的唯一数据源。改这里，所有页面同时更新。
     卡片里不要另抄一份 —— 抄了就会有一天对不上。

   事实来源（改前必须核对，不许凭印象写）：
     · learning-roadmap.md  v4 · 第五节「分阶段路线」+ 第十节「里程碑」
     · 教学进度看板.md      表 2.1（技术栈状态）
     · 每周目标.md          W39
     · E:\物联网\时间线账本.md（物联网线，跨工作区，只写"该线对本线可见的部分"）
   ══════════════════════════════════════════════════════════════════ */
(function (global) {
  'use strict';

  var ANCHOR = '2026-09-23';                 /* 本页数据校准日 */

  function weeksTo(d) {
    var a = new Date(ANCHOR + 'T00:00:00'), b = new Date(d + 'T00:00:00');
    return Math.round((b - a) / 6048e5 * 10) / 10;
  }

  var P = {
    anchor: ANCHOR,
    updated: '2026-09-23',
    weeksTo: weeksTo,

    /* ── 三根尺子：倒推链上的三个硬数 ───────────────────── */
    deadlines: [
      { label: '简历上必须有东西可写', date: '2027-03-01',
        note: '没东西写 → 2027 春投不出实习 → 后面全塌' },
      { label: '考研 / 就业 分岔口', date: '2028-03-01',
        note: '到时候凭实习结果定，不凭感觉' },
      { label: '毕业入职', date: '2029-06-30', note: '—' }
    ],

    /* ── 进度轨道：站名 + 日期 + 到站时"必须已经有什么" ────
       到站要求逐条抄自 learning-roadmap.md 第十节「里程碑（v4 重排）」，
       改动前必须回原表核对。 */
    railSpec: function () {
      return {
        flagLabel: '你在这里 · 还有 ' + Math.round(weeksTo('2027-03-01')) + ' 周',
        stops: [
          { label: '现在', date: '2026.09', state: 'now',
            detail: 'pytest 全绿 ✅ 已达成（27 passed / 0.25s，2026.09.21 实测）。' +
                    '本周 W39 三件事：Linux 任务 1–5 · 项目立项（仓库 + README 三段）· 第 3 课 JOIN。' },
          { label: '项目立项', date: '2026.10',
            detail: '仓库建好 + README 三段：解决什么问题 / 给谁用 / 怎么算做成功了。' },
          { label: '作品 v1', date: '2027.01',
            detail: 'AI 应用 v1 上线公网 + README 里有评测数字 —— 本学年最关键的一个。' +
                    '同期：Linux 15 任务过关（至少微课 1–2）+ SQL JOIN 打通（P-009 转 ✅）。' },
          { label: '简历死线', date: '2027.03',
            detail: '🔴 简历初版（作品 v1 + 评测数字）+ 开始投递。' +
                    '这是整条倒推链上最近的一根死线 —— 现在还剩 ' + Math.round(weeksTo('2027-03-01')) + ' 周。' },
          { label: '第一段实习', date: '2027.07',
            detail: '作品 v2（评估 / 可观测 / 界面）+ 投出 10+ 家。' },
          { label: '分岔口', date: '2028.03',
            detail: '考研 or 就业 —— 凭实习结果定，不凭感觉。同期：飞YOUNG / 星火校园投递。' },
          { label: '秋招', date: '2028.09',
            detail: '简历要有 1–2 段实习 + 1 个能讲 10 分钟的项目。' },
          { label: '毕业入职', date: '2029.06', detail: '—' }
        ]
      };
    },

    /* ── 全局思维导图 ──────────────────────────────────── */
    tree: function () {
      var w = Math.round(weeksTo('2027-03-01'));
      return {
        label: '我的全局', note: '校准 ' + ANCHOR, state: 'root',
        children: [

          { label: '① 时间轴', note: '离简历死线还有 ' + w + ' 周', state: 'doing',
            children: [
              { label: '2026.10 项目立项', note: '🔴 下一个动作 · 仓库 + README 三段', state: 'current' },
              { label: '2027.01 作品 v1 上线公网', note: '本学年最关键的一个', state: 'todo' },
              { label: '2027.03 简历第一根死线', note: '还有 ' + w + ' 周', state: 'todo' },
              { label: '2027.07 第一段实习', state: 'todo' },
              { label: '2028.03 分岔口：考研 / 就业', note: '凭实习结果定', state: 'todo' },
              { label: '2029.06 毕业入职', state: 'todo' }
            ] },

          { label: '② 编程主线', note: '找工作靠这条', state: 'doing',
            children: [
              { label: '已过关', note: 'Git · pytest27 · Docker · FastAPI · Python', state: 'done' },
              { label: '算法 150', note: '模式①② 过关 · 下一步 模式③ 滑动窗口', state: 'doing' },
              { label: 'AI 应用 / RAG', note: '缺口 = 没有从零自己做的应用', state: 'doing' },
              { label: 'SQL / JOIN', note: '第 3 课 ①–④ 已上 · ⑤⑥ 待上', state: 'current' },
              { label: 'Linux', note: '15 个任务待练 · 3 条合肥 JD 要它', state: 'todo' }
            ] },

          { label: '③ 英语线', note: '独立线 · 另有死线 2026-12-12', state: 'doing',
            children: [
              { label: '每日 45 分钟', note: '不计入编程主线的 1.5–2h', state: 'doing' }
            ] },

          { label: '④ 物联网线（导师任务）', note: '独立节奏 · 不占主线名额', state: 'doing',
            children: [
              { label: '最小 Demo 已发出', note: '2026.09.23 发出 · 4 天零信号结束', state: 'done' },
              { label: '等导师回复', note: '他说「找个时间点仔细看看」', state: 'current' },
              { label: '阶段 2 服务发现', note: '等他回话再动', state: 'todo' },
              { label: '毕设位占坑', note: '大三下 2028.02–07 走学院流程', state: 'todo' }
            ] }
        ]
      };
    },

    /* ── 三条纪律（每周目标顶部那三条，放全局页用） ─────── */
    discipline: [
      '按 1.5 h/天排（下限），2 h/天当奖励 —— 别按 2 h 排然后每周欠账',
      '余量不填满，留作意外缓冲',
      '万一周塌了才启用放弃顺序；🔵 发 Demo / ① Linux / ③ JOIN 不砍'
    ]
  };

  /* ══ 复习机制「1-3-7-30」══════════════════════════════════════
     2026-09-23 修复（T-24 / P-015）。教训：上一版只是一张**没日期的表**，
     放在那儿 9 天没人管，第 2 课的 404 三步排查法 17 天后彻底忘光。

     这一版的三条区别：
       ① **日期是算出来的，不是写死的** —— 永远跟着"今天"走，不会过期变废纸
       ② **默认只显示今天该过的** —— 打开就一个动作，不用自己挑
       ③ **逾期会红字跳出来** —— 烂账藏不住，这是防"再烂 9 天"的关键

     ⚠️ 起算日为什么是 09-23 而不是各课的原学习日：第 1、2 课（原 09-06）
        的 1/3/7 三档**全部逾期且从未做过**，实测已经忘光。今晚第 3 课当场
        重测并重讲了其中 3 张 —— **重学即重新起算**，这是诚实的做法，
        不是把旧账一笔勾销。 */
  var REVIEW_START = '2026-09-23';
  function addDays(iso, n) {
    var d = new Date(iso + 'T00:00:00'); d.setDate(d.getDate() + n);
    return d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2);
  }
  P.review = {
    start: REVIEW_START,
    rounds: [1, 3, 7, 30],
    /* 每个复习日的绝对日期（算出来的） */
    dates: function () {
      return P.review.rounds.map(function (n) {
        var iso = addDays(REVIEW_START, n);
        var d = new Date(iso + 'T00:00:00');
        return { n: n, iso: iso, md: (d.getMonth() + 1) + '.' + d.getDate(),
                 w: '日一二三四五六'.charAt(d.getDay()) };
      });
    },
    groups: [
      { course: '第 1 课 · 符号与语法', origin: '2026-09-06', cards: [
        { id: 'c1', q: '`=` 和 `==` 有什么区别？',
          a: '**`=` 是动作，`==` 是问题。** 更本质的区别是**有没有副作用**：`a = 5` 之后 a 变了；`a == 5` 吐出 True，**世界一点没变**。写错 Python 会拦你：`if x = 5:` 直接 SyntaxError。' },
        { id: 'c2', q: '装饰器的 `@` 到底干了什么？',
          a: '**迎宾员登记本**：进门先登记，再放你进去。它不改函数体，只是在外面包一层 —— 所以 `@app.get("/x")` 是"先登记这个路径，再执行下面的函数"。' },
        { id: 'c3', q: '推导式里的 `if` 该放哪？',
          a: '放 **`for` 后面**（那是筛选）：`[x for x in xs if x > 0]`。只有**带 `else` 的才是三元表达式**，那时才写前面。' },
        { id: 'c4', q: '`*` 和 `**` 怎么分？',
          a: '**一星乘、二星方**（`*` 乘、`**` 乘方）；在参数里则是 **`*args` 收位置、`**kwargs` 收关键字**。' }
      ] },
      { course: '第 2 课 · 工程习惯', origin: '2026-09-06', cards: [
        { id: 'c5', q: '浏览器报 404，你的三步排查法是什么？',
          a: '**菜单 → 路径 → 端口**：① 先开 `/docs` 看这个接口**在不在菜单上**（不在 = 你记错了接口名）② 你请求的 URL 和代码里 `@app.get("/xxx")` **一字不差**吗 ③ 两个端口（如 8899 / 8000）是不是**同一个服务**。' },
        { id: 'c6', q: '`commit()` 和 `close()` 分别管什么？忘了哪个才真出事？',
          a: '**`commit()` = 下单（确定落盘）；`close()` = 托盘放回（用完收摊）。**\n\n实测（Python 3.13.9 / SQLite 3.51.0）：\n· `commit ✅ / close ❌` → 另一个连接**读到 1 行**（数据在！）\n· `commit ❌ / close ✅` → **0 行**（丢了）\n\n⇒ **丢数据的是 `commit`，不是 `close`**；`close` 忘写的代价是**占资源**（未关的连接会锁住文件，实测删文件报 WinError 32）。' },
        { id: 'c7', q: 'Pydantic 的 `BaseModel` 是干什么的？数据不合法会怎样？',
          a: '**声明式校验** —— 你在类里写字段和类型，它自动检查。不合法返回 **422**（不是 500）：422 = 你传的东西不对，500 = 我的代码崩了。' }
      ] },
      { course: '第 3 课 · 数据模型与 JOIN', origin: '2026-09-23', cards: [
        { id: 'c8', q: '什么是"绳子表"？为什么多对多必须要第三张表？',
          a: '**绳子的每一行 = 一条关系，不是一个人。**\n\n小明同时在 1 群和 2 群 → 他在绳子表里占**两行**。`joined`（什么时候进的）、`role`（在这个群里是管理员还是成员）也都是**每条绳子各自带一个值** —— 放人表里放不下（一个人加 10 个群要存 10 行），放群表里也放不下（群有 200 人要把群名存 200 遍）。' },
        { id: 'c9', q: '`ON` 和 `WHERE` 有什么区别？',
          a: '**`ON` = 怎么配（配对规则）；`WHERE` = 要哪些（筛选）。**\n\n实测：三表 JOIN **不写 `WHERE`** → 出 **3 行**（所有群的成员都算上）；补上 `WHERE groups.id = 1` → **2 行**。差的就是这一句。' },
        { id: 'c10', q: '`SELECT persons.name FROM persons JOIN group_members ON persons.id = group_members.uid WHERE group_members.gid = 1;` 会出几行？为什么？',
          a: '**2 行。行数 = 配对成功的次数，不是任何一张表里的行数。**\n\n1 号群有 2 个成员 → 配对成功 2 次 → 2 行。' },
        { id: 'c11', q: '找错：`JOIN group_members ON groups.id = group_members.uid` 错在哪？会怎样？',
          a: '**群 id 去对人 id —— 绳子两头接反了。**\n\n两种后果，**都不报错**：\n· id 空间**不重叠**（人 7/9、群 1/2）→ **0 行**，空的，一眼看得出来\n· id 空间**重叠**（两套都从 1 开始编号 —— 你的 `prescriptions.db` 就是）→ **照样出数据，而且看着挺合理** 🔴 这才是最危险的\n\n⇒ 所以 **JOIN 要核对的从来不是语法，是配对对不对**；"不为空"绝不等于"对"。' }
      ] }
    ],
    /* 诊断三步（第 3 课教的迁移技能） */
    diagnosis: [
      '单独数绳子表：`SELECT * FROM prescription_ingredients;`（实测 49 行）',
      '再数 JOIN 的结果行数',
      '🔴 两数一致 **≠** 配对正确 —— 还要**挑一行人工核对内容**（id 重叠时会"数字对、内容全错"）',
      '数字明显对不上（空 / 多很多）→ 几乎一定是 `ON` 写错'
    ]
  };

  global.LabProgress = P;
})(window);
