# 开源学习路线参考清单（外部收集）

> 2026.09 收集 · 与 `learning-roadmap.md`（v3）配合使用
> 用途：为现有个人路线提供体系化知识地图与进阶资源，star 数为 2026.09 查询值
> 教学法证据来源见文末 H 段（`teaching-methodology.md` v2 的依据）

---

## A. 全景地图类 —— 用它做"对照表"

| 资源 | star | 定位 | 用法 |
|------|------|------|------|
| [roadmap.sh](https://roadmap.sh)（仓库 kamranahmedse/developer-roadmap） | ⭐366k | 95+ 条交互式路线图，官方源，持续更新 | 书签第一站；ai-engineer / ai-agents / backend / java / spring-boot / sql / redis / leetcode / docker / linux / vibe-coding 与个人路线逐条对照 |

**roadmap.sh 与本路线最相关的路线**：ai-engineer（RAG/Agents/MCP/Prompt/评估/可观测性）、ai-agents、backend、java、spring-boot、datastructures-and-algorithms、leetcode、sql、redis、docker、linux、prompt-engineering、mlops。

## B. 计算机基础类

| 资源 | star | 定位 | 用法 |
|------|------|------|------|
| [OSSU](https://github.com/ossu/computer-science) | ⭐209k | 完整 CS 学位替代（2 年 × 20h/周，全部免费网课） | 学校课业未覆盖的 Core CS 部分挑着学：系统、网络、理论 |
| [CS50](https://cs50.harvard.edu/x/) | - | 哈佛入门课，免费，每年更新 | 想要"计算机通识"速成时当背景课 |

## C. 算法类（对应大二上主线）

| 资源 | star | 定位 | 用法 |
|------|------|------|------|
| [hello-algo](https://github.com/krahets/hello-algo) | ⭐130k | 算法图解，中文，动画演示 | 刷 LeetCode 150 前先看对应章节，建立直觉 |
| [coding-interview-university](https://github.com/jwasham/coding-interview-university) | ⭐360k | 面试知识体系（数据结构/算法/OS/网络/系统设计） | 期末/面试前系统过一遍 |

## D. AI 应用开发类（对应大二下主线）

| 资源 | star | 定位 | 用法 |
|------|------|------|------|
| roadmap.sh ai-engineer 路线 | - | 从"LLM 如何工作"到 RAG、Agents、MCP、评估、可观测性、本地模型、多模态全流程 | RAG 项目开工前对照此路线确认覆盖度 |
| [ai-engineering-hub](https://github.com/patchy631/ai-engineering-hub) | ⭐37k | LLM/RAG/Agents 教程 + 可运行代码 | 跟练项目 |
| [llm-course](https://github.com/mlabonne/llm-course) | ⭐82k | LLM 系统课程 Roadmap（基础→微调→部署） | 想深入原理时用 |
| [Chip Huyen《AI Engineering》](https://github.com/chiphuyen/aie-book) | ⭐17k | 2025 年出版的 AI 工程师"圣经"，含配套材料 | 大二下精读 |
| [learn-ai-engineering](https://github.com/ashishps1/learn-ai-engineering) | ⭐6k | 免费资源学 AI/LLM，按主题整理 | 补充阅读 |

## E. 深度修炼类（专业度加速器）

| 资源 | star | 定位 | 用法 |
|------|------|------|------|
| [build-your-own-x](https://github.com/codecrafters-io/build-your-own-x) | ⭐545k | 自己写一个 X（数据库/编译器/操作系统/搜索引擎…） | 学完一个专题后"亲手造轮子"验证深度 |
| [TheAlgorithms/Python](https://github.com/TheAlgorithms/Python) | ⭐224k | 经典算法 Python 实现合集 | 查参考实现 |

## F. 中文生态（大二暑假 Java / 前端）

| 资源 | star | 定位 | 用法 |
|------|------|------|------|
| [JavaGuide](https://github.com/Snailclimb/JavaGuide) | ⭐158k | Java 学习+面试指南（中文，持续更新） | 大二暑假学 Java 主线 |
| [Web 前端教程](https://github.com/qianguyihao/Web) | ⭐29k | 前端入门中文教程 | 补 Vue 时用 |

## G. 免费课程平台

| 资源 | star | 定位 |
|------|------|------|
| [freeCodeCamp](https://github.com/freeCodeCamp/freeCodeCamp) | ⭐455k | 免费认证课程，全程实践 |

## H. 教学法 / 学习科学证据来源（教学法 v2 依据）

| 资源 | 证据 | 用法 |
|------|------|------|
| [Nature Reviews Psychology 2022](https://www.nature.com/articles/s44159-022-00089-1) | 间隔 + 检索练习综述 | 教学法 v2 第一、三条原理的依据 |
| [Dunlosky et al. 2013（APS《心理科学》）](https://www.apa.org/pubs/journals/features/stl-0000024.pdf) | 10 种学习技术效应排名：实践测试/间隔练习最高，重读/高亮最低 | 检索练习优先级依据 |
| [ACM 3732791 / Springer 2025 编程教育教学研究](https://dl.acm.org/doi/full/10.1145/3732791) | 示例-问题对 + 引导性自我解释对编程新手的效果（降低认知负荷、提升保持与迁移） | 五步法①②③④的依据 |
| [MIT OCW CMS.595（2024 春，Justin Reich）](https://ocw.mit.edu/courses/cms-595-learning-media-and-technology-spring-2024/) | 认知负荷理论课程（第 2 讲） | 认知负荷原理参考课 |
| [The Learning Scientists](https://www.learningscientists.org/) | 六大学习策略科普（检索/间隔/交错/双重编码/具体例/精加工） | 面向学员的科普材料 |
| [Education Endowment Foundation](https://educationendowmentfoundation.org.uk/) | 认知负荷理论教学应用动画/指南 | 教师读本 |

---

## 与个人路线的映射速查

| 个人路线阶段 | 主用外部资源 |
|--------------|--------------|
| 大二上（算法 + MySQL/Redis + 计网） | hello-algo、roadmap.sh sql/redis/leetcode、CS50（计网背景） |
| 大二下（RAG 项目 + 星火杯） | roadmap.sh ai-engineer 全路线、ai-engineering-hub、AI Engineering 书 |
| 大二暑假（Java + Spring Boot） | JavaGuide、roadmap.sh java/spring-boot |
| 大三（方向专精 + 知识图谱） | roadmap.sh ai-agents/mlops、llm-course、build-your-own-x |

## ⚠️ 说明

- star 数与内容以 2026.09 查询为准，会随开源社区变化
- 第三方"趋势报告"数据（就业率/薪资）仍以官方招聘信息为准，见 learning-roadmap.md 的数据核实提醒
