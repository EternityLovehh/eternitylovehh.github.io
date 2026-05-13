---
title: Rxjava2 线程切换，代替runOnUiThread和handler
date: 2018-12-12 16:18:40
categories:
  - android
tags:
  - rxjava2
---
Rxjava2 线程切换，代替runOnUiThread和handler

rxjava的使用不在这里作更多的说明，已经有很多优秀的文章作了详细的使用说明，这里讲的是如何单拿出一个工具类来作为线程切换使用。  
rxjava线程的调度需要用到ObserveOn和SubscribeOn，官方对于他们的定义是：  
**ObserveOn**  
specify the Scheduler on which an observer will observe this Observable  
指定一个观察者在哪个调度器上观察这个Observable  
**SubscribeOn**  
specify the Scheduler on which an Observable will operate  
指定Observable自身在哪个调度器上执行

通俗的来讲就是ObserveOn是指定的下游事件所在的线程，SubscriberOn是指定上游事件所在的线程，那么显然我们这里需要用到的是ObserveOn.

比如很多设计到ui操作的都必须在主线程，那么这里线程的操作代码如下:

```
 Observable.just(uiTask)
            .observeOn(AndroidSchedulers.mainThread())
            .subscribe(uiTask1 -> uiTask1.doOnUI());
```

Observable.just（）这个方法的意思是当前onNext发送的事件，可以在订阅的时候onNext回调中拿到。  
上面的代码我使用了Consumer，只发送一个订阅。所以看着不是很明确。如果使用observer代码如下：

```
 Observable.just(uiTask)
            .observeOn(AndroidSchedulers.mainThread())
            .subscribe(new Observer<UITask>() {
                @Override
                public void onSubscribe(Disposable d) {
                    
                }
                
                @Override
                public void onNext(UITask uiTask) {
                    uiTask.doOnUI();
                }
                
                @Override
                public void onError(Throwable e) {

                }

                @Override
                public void onComplete() {

                }
            });
```

可以更直观的看出just发送的uitask事件，在消息订阅的onnext回调中就能拿到。当拿到订阅的消息时，这里做一个回调方法，去执行需要执行的操作：

```
   public interface UITask{
    void doOnUI();
}
```

如果你需要切换到子线程，同理代码为：

```
 Observable.just(threadTask)
       .observeOn(Schedulers.io())
       .subscribe(threadTask1 -> threadTask1.doOnThread());
```

完整代码：

```
public class ThreadUtils {

//主线程做操作
public static void doOnUIThread(UITask uiTask){
    Observable.just(uiTask)
            .observeOn(AndroidSchedulers.mainThread())
            .subscribe(uiTask1 -> uiTask1.doOnUI());

 	 }

//io线程做操作
public static void doOnThread(ThreadTask threadTask){
    Observable.just(threadTask)
            .observeOn(Schedulers.io())
            .subscribe(threadTask1 -> threadTask1.doOnThread());
	}

public interface ThreadTask{
    void doOnThread();
   }

 public interface UITask{
      void doOnUI();
  }
}
```

在其他需要的地方进行调用:  
这里是一个需要在主线程进行toast显示

```
ThreadUtils.doOnUIThread(() -> toastShow(msg));
```

如果需要做其他的线程切换都是一样的，首先定义一个接口方法，切换线程后回调这个方法去执行操作。
