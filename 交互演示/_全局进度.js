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

  global.LabProgress = P;
})(window);
