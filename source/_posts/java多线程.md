---
title: java多线程
date: 2021-03-02 15:55:26
tags: java
cover: https://t7.baidu.com/it/u=4162611394,4275913936&fm=193&f=GIF
---

### Thread和Runnable

thread 的实现方式是继承其类，runnable的实现方式是实现其接口，runnable接口支持多继承，thread只能单继承。thread实现了runable接口并进行了扩展，他们之间没有可比性。

### 多线程中的start()和run()

start()方法可以启动线程，使线程处于就绪状态，一旦得到cpu的时间片，就开始执行run方法，run方法结束，线程终止。

run方法只是thread类的一个普通方法调用，还是在主线程执行

### sleep和wait

sleep的实际是thread的native方法，阻塞线程的执行，不会改变线程锁的持有情况

wait方法调用后会进入等待队列，需要在同步代码块中调用，需要其他的线程调用notify释放锁，才能再次进入锁的等待队列

### synchronized关键字

#### synchronized对象锁

```
 public class Test{ 
    // 对象锁：形式1(方法锁) 
    public synchronized void Method1(){ 
        System.out.println("我是对象锁也是方法锁"); 
        try{ 
            Thread.sleep(500); 
        } catch (InterruptedException e){ 
            e.printStackTrace(); 
        } 

    } 
     
    // 对象锁：形式2（代码块形式） 
    public void Method2(){ 
        synchronized (this){ 
            System.out.println("我是对象锁"); 
            try{ 
                Thread.sleep(500); 
            } catch (InterruptedException e){ 
                e.printStackTrace(); 
            } 
        } 
     
    } 

 ｝
```

上述两种方式是一样的，锁住方法体

#### synchronized实现线程间的通信

通过不同的线程共享同一个变量实现线程间的通信

```
public class run  {
​	public static void main (String[] args) {
	  MyObject object = new Object();
	  ThreadA a = new ThreadA(object);
	  ThreadB b = new ThreadB(object);
	  a.start();
	  b.start();
	}
}

class MyObject {
	public synchronized void methodA() {
	
	}
	public synchronized void methodB() {
	
	}

}

class ThreadA extend Thread{
	private MyObject object;
	public ThreadA(MyObject object) {
	}
	
	@override
	public void run() {
		super.run()
		object.methodA();
	}
}

class ThreadB extend Thread{
	private MyObject object;
	public ThreadB(MyObject object) {
	
	}
	
	@override
	public void run() {
		super.run()
		object.methodB();
	}

}
```

### synchronized和volatile

volatiled的本质是告诉jvm当前变量在寄存器中的值是不确定的，需要从主内存中读取，且只能使用在变量上

synchronized 则是锁定当前变量，只有当前线程可以访问该变量，其他线程会被锁住，当前线程改变了之后，其他线程会同步这个变量，synchronized 可以使用在变量、方法和类上。

### synchronized和lock

synchronized是java的内置语言实现，需要托管给jvm执行，synchronized原始采用的是CPU悲观锁机制，即线程获得的是独占锁。独占锁意味着其他线程只能依靠阻塞来等待线程释放锁，当有很多线程竞争锁的时候，会引起cpu频繁上下文切换导致效率低，synchronized是非公平锁，不能保证线程等待的顺序

lock是java写的控制锁代码，lock采用乐观锁机制，每次不加锁而是假设没有冲突去完成某项操作，如果因为冲突失败就重试，直到成功为止。lock必须在代码中手动unlock释放锁，否则会造成死锁。lock可通过实例化ReentrantLock true or false来实现公平锁和非公平锁。

在jdk1.6之后。两者使用的性能差别上不大

### 线程池

#### 使用线程池的好处

1. 线程池降低资源消耗，重复利用已经创建的线程，降低线程创建和销毁造成的消耗
2. 提高响应速度，通过复用已存在的线程，无需等待新线程的创建便能立即执行
3. 提高线程的可管理性，因为线程若是无限制的创建，可能会导致内存占用过多而产生OOM，并且会造成cpu过度切换

```cpp
public ThreadPoolExecutor(int corePoolSize, int maximumPoolSize, long keepAliveTime, TimeUnit unit, BlockingQueue<Runnable> workQueue) {
    this(corePoolSize, maximumPoolSize, keepAliveTime, unit, workQueue,
         Executors.defaultThreadFactory(), defaultHandler);
}
```

#### 线程池流程

1. 当有新的任务到来，首先判断核心线程池是否已满，没满则创建一个新的工作线程执行任务，已满则
2. 判断任务队列是否已满，没满将任务添加到工作队列等待，已满则
3. 判断整个线程池中的线程数是否大于最大线程数，小于则创建一个新的工作线程执行任务，已满则
4. 执行饱和策略，抛出异常或者不执行、

#### 线程池为什么要使用阻塞队列而不使用非阻塞队列？

阻塞队列可以保证任务队列中没有任务时阻塞获取任务的线程，使线程进入wait状态，释放cpu资源，当队列中有任务时才唤醒对应线程从队列中取出消息进行执行，使得线程不会一直占用cpu资源