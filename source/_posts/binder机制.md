---
title: binder通信机制
date: 2021-02-25 13:44:20
tags:
---

### 安卓为什么要使用binder通信？

1. 采用C/S的通信模式

2. binder对比linux的通信机制，有以下优点：

   scoket 是一个通用接口，导致其传输速率低，开销大；

   管道和消息队列  采取存储转发方式，至少需要拷贝2次数据，效率低， 而binder只需要一次数据拷贝；

   共享内存 虽然在传输时没有拷贝数据，但是控制机制复杂。

   

3. 安全性更高 ，binder机制的uid/pid 是由binder机制本身在内核空间添加身份标识，安全性高，并且binder机制可以建立私有通道。

### binder通信机制流程

![](E:\github\myblog\source\images\20160607091016312.jpg)

从图中可以看到，binder的通信框架包含了四个重要的角色： Server， Client， ServerManager和binder驱动；client 和server是存在于用户空间，它们之间的通信是由binder驱动在内核空间实现的，而ServerManager作为守护进程也存在于用户空间，处理客户端请求和管理所有的服务项， binder驱动工作在内核中，负责进程间通信的建立。

#### binder通信原理

binder通信只需要copy一次数据的原理是使用了内存映射 mmap() 

##### 内存映射

1.首先binder驱动在内核空间创建一个数据接收缓存区，

2.接着在内核空间开辟一块内核缓存区，用于接收进程发送的数据

3.实现内存映射，内核缓存区和接收进程的用户空间地址都映射到同一个接收缓存区

4.发送进程通过系统调用copy_from_user()将数据copy到内核中的内核缓存区

5.由于内核缓存区和接收进程的用户空间存在内存映射，因此也就相当于把数据发送到了接收进程的用户空间。

![img](E:\github\myblog\source\images\960a304e251f95cab5a46f4f25c7df3b650952c8.jpeg)

##### binder通信过程

Client要和Server通信，它就是通过保存一个Server对象的Binder引用，再通过该Binder引用在内核中找到对应的Binder实体，进而找到Server对象，然后将通信内容发送给Server对象。

   1.Server首先会向binder驱动发起注册请求，而binder驱动在收到请求之后会新建一个该server对应的	  binder实体和binder的引用，然后将server的名字和binder的引用打包传递给ServerManager进程

2. 当ServerManger收到数据后，会将Server的名字和binder引用注册到一张查找表中
3. 当client 向binder驱动发起获取服务的请求，那么ServerManger就可以在查找表中找到对应的Server的binder引用，并将binder引用返回给Client，Client就可以利用获得的binder引用来使用远程服务了

