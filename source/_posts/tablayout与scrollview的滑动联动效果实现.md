---
title: tablayout与scrollview的滑动联动效果实现
date: 2018-04-09 13:57:37
categories:
  - android
---
**\*tablayout与scrollview的滑动联动效果实现**   
本次要实现的效果是点击标题栏tablayout的tab，下方的scrollview布局滚动到指定的位置，当下面的布局上滑到一定位置时，tab的文字颜色变化。效果图如下:   
![这里写图片描述](/images/posts/csdn-79865518-1.gif)   
因为这里是用的模拟器进行的操作，所以效果上看起来有些卡顿。   
1. 首先这里标题栏是使用的安卓原生的**tablayout**布局实现三个tab切换的效果，下面的布局是一个很简单的**Scrollview**控件实现可上下滑动的布局。下面是标题栏的布局文件：

```
    <android.support.design.widget.AppBarLayout
        android:id="@+id/top_appbar"
        android:layout_width="match_parent"
        android:layout_height="wrap_content">
        <android.support.v7.widget.Toolbar
            android:id="@+id/toolbar"
            android:layout_width="match_parent"
            android:layout_height="@dimen/sn_44dp"
            android:background="@color/tabColor"
            android:theme="@style/ThemeOverlay.AppCompat.ActionBar"
            app:popupTheme="@style/ThemeOverlay.AppCompat.Light"
            app:contentInsetStart="0dp">
            <LinearLayout
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:orientation="horizontal">
                <LinearLayout
                    android:id="@+id/ll_left_img"
                    android:layout_width="wrap_content"
                    android:layout_height="match_parent">
                    <ImageView
                        android:id="@+id/goods_info_back"
                        android:layout_width="match_parent"
                        android:layout_height="@dimen/sn_22dp"
                        android:layout_gravity="center"
                        android:layout_weight="6.5"
                        android:src="@drawable/search_back"
                        android:layout_marginLeft="@dimen/sn_28dp"
                        android:layout_marginRight="@dimen/sn_8dp"/>
                </LinearLayout>
                <android.support.design.widget.TabLayout
                    android:id="@+id/goods_tab_layout"
                    android:layout_width="match_parent"
                    android:layout_height="wrap_content"
                    android:minHeight="?attr/actionBarSize"
                    app:tabSelectedTextColor="@color/mall_color"
                    app:tabTextColor="@android:color/black"
                    app:tabIndicatorColor="@android:color/transparent"
                    app:tabGravity="center"
                    android:layout_weight="2">
                </android.support.design.widget.TabLayout>
                <LinearLayout
                    android:id="@+id/ll_right_img"
                    android:layout_width="wrap_content"
                    android:layout_height="match_parent">
                    <ImageView
                        android:id="@+id/goods_info_msg"
                        android:layout_width="match_parent"
                        android:layout_height="@dimen/sn_22dp"
                        android:src="@drawable/more_menu"
                        android:layout_weight="6.5"
                        android:layout_gravity="center"
                        android:layout_marginLeft="@dimen/sn_8dp"
                        android:layout_marginRight="@dimen/sn_28dp"/>
                </LinearLayout>
            </LinearLayout>
        </android.support.v7.widget.Toolbar>
    </android.support.design.widget.AppBarLayout>
```

这里关于tablayout只是实现了简单的切换效果，我就不多做说明了   
2.下面布局由 商品轮播图， 商品详情， 商品评价和推荐商品四个部分组成，然后包裹在一个scorllview中，布局文件很简单，但是比较冗长，我这里不贴出了。   
首先处理tablayout的点击切换事件，添加addOnTabSelectedListener监听

```
//tablayout监听事件
        goodsTabLayout.addOnTabSelectedListener(new TabLayout.OnTabSelectedListener() {
            @Override
            public void onTabSelected(TabLayout.Tab tab) {
                int pos = tab.getPosition();
                //表明当前的动作是由 TabLayout 触发和主导
                tagFlag = false;
                if (pos == 0) {
                    mainNestScroll.smoothScrollTo(0, scrollGoods.getTop());
                }
                if (pos == 1) {
                    mainNestScroll.smoothScrollTo(0, scrollDetail.getTop());
                }
                if (pos == 2) {
                    mainNestScroll.smoothScrollTo(0, scrollComment.getTop());
                }
            }
            @Override
            public void onTabUnselected(TabLayout.Tab tab) {
                Log.i("tab", "onTabUnselected: " + tab.getPosition());
            }
            @Override
            public void onTabReselected(TabLayout.Tab tab) {
                Log.i("tab", "onTabReselected: " + tab.getPosition());
            }
        });
```

当点击相应的tab选项时，调用scrollview的smoothScrollTo方法来实现布局滚动到顶部的效果。getTop方法拿到当前控件的顶部坐标。   
3.上面实现了点击tab选项，布局的滑动效果，那么当布局在滑动到顶端时，tab选项的切换应该怎么去实现呢， 这里如果仅仅只是去判断当前布局是否置顶，然后去设置tab选项卡的颜色，是没有作用的。   
这里需要定义一个**tagFlag**去判断当前的动作是 scrollview 主导还是 tablayout 主导， 通过 mainNestScroll.getScrollY() 获得 ScrollView 滑动距离，判断 ScrollView 当前展示的顶部内容属于哪个内容模块，具体的实现代码如下:

```
 /**
     * 是否是ScrollView主动动作
     * false:是ScrollView主动动作
     * true:是TabLayout 主动动作
     */
    private boolean tagFlag = false;
    /**
     * 用于切换内容模块，相应的改变导航标签，表示当一个所处的位置
     */
    private int lastTagIndex = 0;
    /**
     * 用于在同一个内容模块内滑动，锁定导航标签，防止重复刷新标签
     * true: 锁定
     * false ; 没有锁定
     */
    private boolean content2NavigateFlagInnerLock = false;

    mainNestScroll.getViewTreeObserver().addOnScrollChangedListener(() -> {
            tagFlag = true;
            if (mainNestScroll.getScrollY() > scrollDetail.getTop()) {
                refreshContent2NavigationFlag(2);
            } else if (mainNestScroll.getScrollY() > scrollComment.getTop()) {
                refreshContent2NavigationFlag(3);
            } else if (mainNestScroll.getScrollY() > scrollGoods.getTop()) {
                refreshContent2NavigationFlag(1);
            } else {
                refreshContent2NavigationFlag(0);
            }
      });

     /**
     * 刷新标签
     *
     * @param currentTagIndex 当前模块位置
     */
    private void refreshContent2NavigationFlag(int currentTagIndex) {
        // 上一个位置与当前位置不一致是，解锁内部锁，是导航可以发生变化
        if (lastTagIndex != currentTagIndex) {
            content2NavigateFlagInnerLock = false;
        }
        if (!content2NavigateFlagInnerLock) {
            // 锁定内部锁
            content2NavigateFlagInnerLock = true;
            // 动作是由ScrollView触发主导的情况下，导航标签才可以滚动选中
            if (tagFlag) {
                goodsTabLayout.setScrollPosition(currentTagIndex, 0, true);
            }
        }
        lastTagIndex = currentTagIndex;
    }
```

以上关于scrollview与tablayout的联动效果实现，是自己在做项目时遇到的一点小问题，当不加内部锁判断动作主体时，无法实现滑动切换tab的效果，作为一个简单的实现记录。
