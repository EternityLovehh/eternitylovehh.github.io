---
title: Activity启动流程
date: 2021-03-01 18:38:48
tags: Android
---

Activity启动流程分为两种：

1. 启动正在运行App中的Activity，默认和启动该Activity的上级页面处于同一进程。
2. launcher启动新的Activity

### 具体流程

![](images/20190806171917409.png)

1. Launcher通知AMS要启动Activity

   startActivitySafely->startActivity->Instrumentation.execStartActivity()(AMP.startActivity)->AMS.startActivity

2. PMS的resoveIntent验证要启动activity是否匹配，如果匹配，AMS会通知Launcher所在的主线程，暂停当前的Activity（Launcher）

3. pause完activity后，通知AMS已经paused
4. 判断要启动的Activity进程是否存在？存在，发送消息LAUNCH_ACTIVITY给需要启动的Activity主线程，执行handleLaunchActivity。不存在，通过socket向zygote请求创建进程
5. 创建ActivityThread实例，执行初始化操作并绑定Application，如果Application不存在，会调用LoadApk.makeApplication创建一个新的Application对象，在主线程中通过thread.attach方法来关联ApplicationThread，之后进入loop循环
6. 处理新的应用进程发出的创建进程完成的通信请求，并通知新应用程序进程启动目标Activity组件。
7. 调用performLaunchActivity，instrumentation.execStartActivity 加载MainActivity类，调用oncreate声明周期方法