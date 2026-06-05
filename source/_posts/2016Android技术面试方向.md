---
title: 2016Android面试方向
date: 2026-06-05 14:00:00
tags: [Android, java]
categories: [技术]
---

基于对真实社区与市场平台（Reddit/ProAndroidDev、牛客网、知乎、掘金、CSDN、GitHub 面试题库、CoderScreen、各公司招聘指南）的检索，下面是 AI 盛行时代 Android
  开发面试的真实聚焦方向。需要先说明一点：海外（FAANG/欧美）和国内大厂的侧重点差异明显，我分开讲。

AI 时代 Android 开发面试聚焦方向（2025–2026）
基于 Reddit / ProAndroidDev、牛客网、知乎、掘金、CSDN、GitHub 面试题库、CoderScreen、各公司招聘指南的真实检索。

一、AI 时代：面试形式的具体变化
1. 已经发生的事实（真实公司做法）
公司	2025–2026 的实际做法
Canva	2025年6月起，明确要求前后端/ML 候选人在技术面用 Copilot/Cursor/Claude
Meta	让候选人自选 AI 模型辅助
Google	试点 AI 辅助编码面，指定用 Gemini
2. 面试官实际评估的维度（会写进评分表）
Prompt 能力：能否把模糊需求拆成 AI 能干的明确子任务

Output validation：AI 给的代码能否一眼看出哪里错、边界没覆盖

主导权：是你在用 AI 解决你设计的方案，还是 AI 给啥你抄啥

明确的负面信号：过度依赖 AI、讲不清自己理解 → 直接挂

3. 真实追问示例
“你刚才让 AI 生成了这段协程代码，它这里用了 GlobalScope，你觉得有没有问题？”（考你会不会盲信）
“如果让你不用 AI，把这个函数的时间复杂度讲一遍。”
“AI 给的方案在百万级数据下会怎样？”（AI 通常不主动考虑规模）

4. 备战动作
练习 边用 AI 边解说自己的判断。把“我为什么接受/拒绝这段 AI 输出”说出口，这是新的区分度。

二、Kotlin 协程（必问，且越问越深）
入门层（筛人用）
suspend 函数和普通函数区别？

launch vs async 区别？async 的 Deferred 怎么拿结果？

深挖链（区分高下）
结构化并发：什么是 structured concurrency？

追问：父协程为什么必须等所有子协程完成？

追问：一个子协程抛异常，默认会发生什么？
→ 答：取消父和所有兄弟协程

追问：那我不想让一个子失败拖垮其他怎么办？
→ 答：supervisorScope / SupervisorJob

取消机制：协程取消是什么特性？
→ 取消是协作式（cooperative）的，Job 被 cancel 后，协程要在挂起点或主动检查（isActive / ensureActive / yield）时才真正停

追问：你写了个 while 循环做计算，cancel 不掉，怎么办？

追问：在 finally 里还要做挂起调用（如关资源）怎么办？
→ 答：withContext(NonCancellable)

viewModelScope 为什么防泄漏
→ ViewModel 的 onCleared() 时自动 cancel 该 scope 下所有协程

Dispatchers：IO / Default / Main 各自场景？Dispatchers.IO 底层线程池怎么回事？

Exception handling：try-catch 抓不到 launch 里的异常？CoroutineExceptionHandler 用在哪？async 的异常什么时候抛？

三、Flow（已取代 LiveData，几乎必问）
核心对比题（高频）
冷流 vs 热流，举例

StateFlow vs SharedFlow 区别？分别什么场景？

StateFlow：有初始值、有 conflate、状态型（UI state）

SharedFlow：可配 replay/buffer，事件型（一次性事件如 toast/导航）

StateFlow vs LiveData 区别？为什么团队迁移到 StateFlow？

深挖点
在 UI 层怎么收集 Flow 才不浪费资源？
→ 答：repeatOnLifecycle(STARTED) / flowWithLifecycle，后台时停止收集

操作符：map / flatMapLatest / debounce / combine 的实际用途（搜索框防抖是经典场景）

背压（backpressure）在 Flow 里怎么处理？buffer / conflate / collectLatest 区别？

四、Jetpack Compose（新项目默认 UI 标准）
状态管理（最高频）
remember 和 rememberSaveable 区别？后者怎么跨配置变更/进程恢复存？

mutableStateOf 怎么触发重组？

derivedStateOf 解决什么问题？什么时候必须用它？
→ 派生状态、避免不必要重组

状态提升（state hoisting）：为什么要把 state 提到父级？无状态 composable 好处？
→ 可测、可复用、单向数据流

重组与性能（区分中高级）
recomposition 是什么？什么会触发？

为什么 Compose 列表里要用 key？不稳定参数（unstable）导致的过度重组怎么排查？

@Stable / @Immutable 注解作用？

LazyColumn 性能优化点（key、contentType、避免在 composition 里做重计算）

副作用（必考一组）
LaunchedEffect / rememberCoroutineScope / DisposableEffect / SideEffect 分别什么时候用？

LaunchedEffect(key) 的 key 变化会发生什么？

互操作 & 其他
Compose 和传统 View 怎么互相嵌套（AndroidView / ComposeView）？

Compose 的导航（NavHost）怎么传参、怎么传复杂对象？
→ 不建议传大对象，传 ID

五、架构（中高级必问）
MVVM vs MVI vs MVP 三者取舍，为什么新项目倾向 MVI？
→ 单一不可变 state、单向数据流、事件可追溯、易测试

UDF（单向数据流） 怎么落地？

ViewModel 如何在屏幕旋转中存活？SavedStateHandle 解决什么？

依赖注入：Hilt 的 scope（@Singleton / @ViewModelScoped）

注意：你们项目用 Dspi，不用 Hilt —— 但面试市场普遍考 Hilt/Dagger

分层：data/domain/presentation，Repository 模式，UseCase 该不该有

模块化：怎么拆模块？模块间循环依赖怎么解（国内高频）？按 feature 还是按 layer 拆？

六、移动系统设计（海外资深岗核心，国内逐渐增加）
经典题目
设计一个类 Google Photos（上传、缩略图、离线）

设计聊天应用（消息已读、离线消息、顺序保证）

设计 Feed 流（分页、缓存、预取、图片加载）

设计文件/图片上传管线（断点续传、重试、并发控制）

答题必须覆盖的维度（面试官 checklist）
维度	要点说明
网络协议选型	REST / WebSocket / SSE / Push，为什么选这个
存储	关系型(Room) / 文件 / KV(MMKV/DataStore)，怎么选
Offline-First	本地 DB 作为 single source of truth；Room 既是缓存也是离线操作队列
同步与幂等	客户端生成 request ID + 服务端去重 + Idempotency-Key 头
冲突解决	last-write-wins / 版本号 / 复杂场景 OT
可靠后台任务	WorkManager + Room + NetworkCallback 组合
缓存策略	内存 + 磁盘多级、缓存失效、预取分页
push 同步 vs pull 同步	取舍
七、性能优化（国内大厂第一高频，“你做过哪些优化”必问）
五大块及深挖点
1. 启动优化（经典：“冷启动 4s → 800ms 怎么做”）
冷/温/热启动区别

手段：延迟初始化、App Startup 库、异步初始化、闪屏优化、减少 Application.onCreate 工作量、Baseline Profiles

测量：adb shell am start -W、Perfetto、reportFullyDrawn

2. 内存优化 / 泄漏
常见泄漏：Handler 持有 Activity、静态持有 Context、未注销监听、内部类

工具：LeakCanary、Memory Profiler、adb shell dumpsys meminfo

Bitmap 优化（采样、复用、格式）

3. 卡顿 / 掉帧
为什么掉帧（主线程耗时 > 16ms）

工具：Systrace/Perfetto、Choreographer、BlockCanary

过度绘制、布局层级、measure/layout 优化

4. 耗电优化
唤醒锁、定位频率、WorkManager 约束、Doze 模式

5. APK 瘦身
资源混淆、R8/ProGuard、so 拆分(abi split)、App Bundle、图片 webp/无用资源

八、源码 / 底层原理（国内大厂特色，海外几乎不问）
Binder：为什么用 Binder？一次内存拷贝（mmap）原理？和传统 IPC 多次拷贝对比

Handler/Looper/MessageQueue：消息机制全流程；为什么主线程 Looper.loop 死循环不卡 ANR；Handler 内存泄漏原理与修复

事件分发：dispatchTouchEvent / onInterceptTouchEvent / onTouchEvent 的传递与拦截，滑动冲突解决

应用启动流程：从点击图标到首帧（Launcher → AMS → Zygote fork → Application → Activity）

第三方库源码：

OkHttp：拦截器链（责任链模式）、连接池、缓存

Retrofit：动态代理 + 注解解析

Glide：生命周期绑定、三级缓存、Bitmap 复用池

九、AI 相关加分项（新兴，不是主考但越来越值钱）
端侧 AI：ML Kit（OCR/人脸/翻译）、端侧模型部署，平衡延迟与成本、模型量化

应用内 LLM / RAG 集成：海外已成独立面试品类（设计 RAG 问答助手、AI 客服 + 人工兜底升级路径）

新关键词（2025 Q4 招聘出现）：MCP / A2A 协议熟悉度成加分项

AI 工具工程化：能讲清你在真实项目里怎么用 Copilot/Cursor 提效、怎么 review AI 代码

十、行为面 & 软技能（别忽略，常是最终决定项）
项目深挖：“这个项目最难的技术点？你的决策依据？”（国内尤其爱挖项目）

设计取舍能力：随着 AI 接管常规活，架构判断力被下放到每个层级

沟通：系统设计面里“能不能讲清 trade-off”权重极高

总结：优先级地图
层级	海外大厂	国内大厂
必考地基	Kotlin 协程 / Flow / Compose / 架构	同左 + Java 基础
核心战场	移动系统设计（离线、同步、缓存）	性能优化 + 源码（Binder/Handler/启动）
形式变化	允许用 AI，考 AI 协作与判断力	逐步跟进，仍偏八股 + 项目深挖
加分项	GenAI 系统设计、端侧 AI	端侧 AI、组件化、跨端(Flutter/RN)
给准备者的真实建议
八股要懂原理（不是背）

重点投入系统设计（海外）或性能优化+源码（国内）

刻意练习 “如何用 AI 高效解题且能讲清自己的判断” —— 这是 AI 时代区别于纯背题选手的关键

参考来源：
  - 125 Android/Kotlin Interview Questions 2026 — Curotec
  - Top 50 Android Developer Interview Questions — Index.dev
  - amitshekhariitbhu/android-interview-questions (GitHub)
  - anandwana001/android-interview (GitHub)
  - Android System Design Interview Questions — ProAndroidDev
  - weeeBox/mobile-system-design (GitHub)
  - The Mobile Engineer's Guide to System Design Interviews — systemdesign.one
  - Offline-First Mobile App Architecture — DEV Community
  - State of Technical Interviews 2025: AI Revolution — CoderScreen
  - Google's AI-Assisted Coding Interview 2026 Guide — Exponent
  - Meta transformed their coding interviews with AI — Medium
  - 2025大厂Android面试直通车：源码解析+性能优化高频考点 — 腾讯云
  - Android 面试官："你做过哪些性能优化？" — 知乎
  - Android面试话题 — 牛客网