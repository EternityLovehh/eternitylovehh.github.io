---
title: handle消息处理机制
date: 2021-02-22 17:19:37
tags:
---

### Handler

Handler 构造方法中会默认关联当前线程的Looper对象，一个线程只能有一个Looper对象，但是可以有多个handler关联这个looper对象，handler也提供一些构造方法关联自定义的Looper对象。子线程中默认是没有开启looper轮循器的，没有关联的messageQueue管理消息。在子线程中创建handler，需要在looper.prepare() 之后，looper.loop()之前。

### Looper

Looper即消息循环器，它可以将一个普通线程转换为一个Looper线程， Looper.prepare()方法将线程初始化为Looper线程，该方法在线程中将Looper对象定义为ThreadLocal对象，使得looper对象成为该线程的私有对象。ThreadLocal可以包装一个对象，使其成为线程私有的局部变量，通过ThreadLocal的get和set方法来访问这个线程局部变量，而不受其他线程的影响。

### Message

message应该使用Message.obtain()方法从一个全局的消息池中得到空的message对象，这样可以有效的节省系统资源

### MessageQueue

MessageQueue.enqueueMessage()方法是所有消息发送方法的最终调用点，发送的消息最后都会直接插入到对应的消息队列中。MessageQueue.next() 方法可以从消息队列中取出一个需处理的消息，在没有消息或者消息还未到时，该方法会阻塞线程，等待消息通过MessageQueue.enqueueMessage()方法入队后唤醒线程。

handle发送延迟消息 其实是直接发送消息，再借MessageQueue.next() 和MessageQueue.enqueueMessage()两个方法，通过native方法阻塞线程一定时间，等待消息的执行时间到后再取出消息执行。

### Handler消息传递机制

实例化一个handler对象，调用sendMessage方法发送消息到MessageQueue消息队列中，主线程默认执行了Looper.loop()方法开启线程的循环模式，调用dispatchMessage方法，获取message，并调用handleMessage方法处理消息，完成UI的更新。

### 为什么主线程不会因为 `Looper.loop()` 里的死循环卡死？

 对于cpu来说，线程和进程都是一段可执行代码，cpu采用cfs调度算法保证每个执行任务都尽可能公平的享有cpu时间片段，所以只要创建了其他新线程处理事务，主线程就不会导致系统卡死。运行在主线程的ActivityThread中的mian() 方法中就创建了新的Binder线程ApplicationThread ， 用于接收系统服务AMS发来的事件。loop方法，在主线程没有MessageQueue没有消息时，就会阻塞在next方法中的nativePollOnce() 方法里。此时主线程会释放cpu资源进入休眠状态，直到下个消息到达，通过Io多路复用机制同时监控多个描述符，当某个读或写就绪，就会立即通知相应程序进行操作，即读写是阻塞的。所以主线程大多数时候就是休眠的，不会消耗大量的cpu资源。

### 能否在子线程更新 UI ？为什么 `onCreate()` 中的子线程更新 UI 有时可以成功？

在oncreate中新建一个线程立即执行操作ui，是可以正常运行的，如果延迟一段时间执行就会抛出异常，因为检测线程的方法checkThread() 是在ViewRootImpl中被调用，而ViewRootImpl是在ActivityThread的handleResumeActivity时被添加，也就是在onresume中执行checkThread()。所以在oncreate中更新ui有时是可以成功的。

### 非静态类的 Handler 导致内存泄漏

非静态内部类、匿名内部类、局部内部类都会隐式的持有期外部类的引用，在主线程使用handler的时候，handler会默认绑定这个线程的Looper对象，Looper线程的生命周期贯穿整个主线程的生命周期，所以当looper对象中的MessageQueue里还有未处理完的message时，因为每个message都持有handler的引，所以handler无法被回收，其持有引用的外部类也无法回收，造成泄漏。

###### 解决办法：静态内部类+弱引用的方式

```
private Handler sHandler = new TestHandler(this);

static class TestHandler extends Handler {

​	private WeakReference<Activity> reference;

​	TestHandler(Activity activity) {
​		 reference = new WeakReference<>(activity);
​	}

​	@Override
​	public void handleMessage(Message msg)  {
​		super.handleMessage(msg);
​		Activity activity = reference.get();
​		if (activity != null && !activity.isFinishing() ) {
​			switch(msg.what) {
​				//处理消息
​			}
​		}
​	}
}
```

###### 在外部类对象被销毁时，将消息队列清空

```
@Override 
protected void onDestroy() {   
   handler.removeCallbacksAndMessages(null);    
   super.onDestroy(); 
}
```

### 消息插队

当需要发送一个插队消息，会在消息对中插入一个target为空的message，在取出消息时如果发现了这个消息，就跳过队列中所有的消息（阻塞块停止正常的队列），返回这个的消息，然后将这个标记消息从队列中remove。

### HandlerThread

1. handlerThread 本质上是一个线程类，它继承了thread
2. handlerThread 有自己内部的Looper对象，可以进行looper循环
3. 通过获取handlerThread的looper对象传递给handler对象，可以在handleMessage方法中执行异步任务
4. 优点 是不会堵塞ui线程，减少了对性能的消耗，缺点是不能同时进行多任务的处理，需要等待进行处理
5. 与线程池注重并发不同，handlerThread是一个串行队列，HandlerThread 背后只有一个线程