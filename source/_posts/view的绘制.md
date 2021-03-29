---
title: 事件分发机制和冲突处理
date: 2021-02-26 15:02:05
tags: Android
---

### Android 事件的传递和分发机制

事件的传递是从Activity开始的，基于从上到下的树形传递原则：Activity -->PhoneWindow–>DectorView–>ViewGroup–>View

事件的优先级onTouchListener->onTouchEvent->onClicklistener

![](https://upload-images.jianshu.io/upload_images/966283-b9cb65aceea9219b.png?imageMogr2/auto-orient/strip|imageView2/2/w/885/format/webp)

#### ViewGroup

主要包括dispatchTouchEvent()，onInterceptTouchEvent()， onTouchEvent()三个方法。ViewGroup默认是不拦截事件的

#### View 

主要包括dispatchTouchEvent()， onTouchEvent()两个方法，它不具备拦截事件的能力，传递到子view中的事件，要么被消费掉，要么不消费向上级回传。view的onTouchEvent(）方法默认会消费掉事件

#### 事件的传递和分发流程

当一个点击事件发生时，首先调用Activity的dispatchTouchEvent()方法，

1. return super.dispatchTouchEvent(ev)事件继续传递到getWindow().superDispatchTouchEvent()和mDecorView.superDispatchTouchEvent()直到下一级ViewGroup
2. return true 或者return false  表示事件已经被消费掉。

传递到viewGroup的dispatchTouchEvent() 方法后，

1. 如果return true表示事件消费掉了

2. reurn fasle 事件会回传给父控件的OnTouchEvent处理

3. return super则事件会调用onInterceptTouchEvent()方法询问是否需要拦截该事件

   1). InterceptTouchEvent() 方法 return true 表示拦截事件并交给onTouchEvent（）方法进行处理  return true 表示事件消费，return false  和super  则回传给父控件的OnTouchEvent处理

   2). InterceptTouchEvent() 方法 return false，super表示不拦截，事件继续向下传递

事件传递到view的dispatchTouchEvent() 方法

1. return true 表示事件被消费

2. return false 则回传事件给上一级view的OnTouchEvent

3. return super 则会调用该view的onTouchEvent方法进行处理

   1). onTouchEvent  return true ， super表示事件被消费

   2). return false 则事件回传给上一级OnTouchEvent进行处理

事件如果传递到最后一级子View

1. 事件还没有被消费掉reurn false，则该事件会从下往上回传给父view的onTouchEvent 进行处理
2. 事件被消费掉了return true ，则该事件会从下往上回传到dispatchTouchEvent（）方法，告诉上层，事件已经被消费掉了

### 滑动冲突的解决方案

#### 外部拦截法

外部拦截法是指事件都先经过父容器的拦截处理，需要重写父容器的onInterceptTouchEvent方法，在内部判断如果需要此事件就进行拦截

#### 内部拦截法

内部拦截法是指父容器不拦截任何事件，所有的事件都传递给子元素，如果子元素需要则消费掉，如果子元素不需要这个事件，则重写子元素的dispatchTouchEvent方法，并调用getParent().requestDisallowInterceptTouchEvent()方法交给父容器处理，然后修改父容器的onInterceptTouchEvent，对应的点击操作 return false表示不拦截事件。