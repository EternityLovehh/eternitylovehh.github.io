---
title: Android 4.4及以上版本写入外置SD卡问题
date: 2017-06-02 14:13:59
categories:
  - android
tags:
  - android
  - 手机
  - 内存
  - sdk
cover: /images/posts/csdn-72843868-1.png
---
**1 获取外置SD卡的路径**   
 由于现在大多数手机都是带有内存的，原本获取外置SD卡路径的方法`Environment.getExternalStorageDirectory()` 获取得到的是手机自身内存的根目录。那么我们要怎么来获取到外置SD卡的路径，首先需要判断是否挂载了sdk，同样的Environment.getExternalStorageState()这个方法判断的只是机身内存空间，需要额外写一个工具类进行判断。这里要用到的是java的反射机制，下面是代码：

```
public class SDMountUtil {
    /**
     * 判断是否挂载外置sd卡
     * @param context
     * @return
     */
    public static boolean sdMounted(Context context){
        boolean mounted=false;
        StorageManager sm=(StorageManager)context.getSystemService(Context.STORAGE_SERVICE);
        try {
            Method getVolumList=StorageManager.class.getMethod("getVolumeList");
            getVolumList.setAccessible(true);
            Object []results=(Object[]) getVolumList.invoke(sm);
            if(results!=null){
                for(Object result:results){
                    Method mRemoveable=result.getClass().getMethod("isRemovable");
                    Boolean isRemovable=(Boolean) mRemoveable.invoke(result);
                    if(isRemovable){
                        Method getPath=result.getClass().getMethod("getPath");
                        String path=(String) getPath.invoke(result);
                        Method getState=sm.getClass().getMethod("getVolumeState", String.class);
                        String state=(String) getState.invoke(sm, path);
                        if(state.equals(Environment.MEDIA_MOUNTED)){
                            mounted=true;
                            break;
                        }

                    }
                }
            }
        } catch (NoSuchMethodException e) {
            e.printStackTrace();
        } catch (IllegalAccessException e) {
            e.printStackTrace();
        } catch (IllegalArgumentException e) {
            e.printStackTrace();
        } catch (InvocationTargetException e) {
            e.printStackTrace();
        }
        return mounted;
    }
}
```

判断是否挂载外置sd卡后，如果有外置sd卡再去获取路径

```
package com.example.testsd;

import java.lang.reflect.Array;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;

import android.content.Context;
import android.os.Environment;
import android.os.storage.StorageManager;

public class SDCardPath {
    public  String cardPath;
    public  String mPath;
    private  Context mContext;

    public SDCardPath(Context context) {
        mContext=context.getApplicationContext();
    }
    /**
     * SD卡目录下的文件存放路径
     * @return
     */
    public String getCardPath() {
        //判断是否存在外置SD卡
        boolean state=SDMountUtil.sdMounted(mContext);
        //如果存在SD卡，则mpath为外置SD卡目录下，若不存在SD卡，则在内置SD卡目录下
        cardPath=getExtSDCardPath(mContext, state);
        mPath=cardPath+"/Android/data/"+mContext.getPackageName()+"/files"; 
        return mPath;
    }
    /**
     * 获取外置SD卡根路径
     * @param mContext
     * @param is_removable 是否存在外置SD卡
     * @return
     */
    private  String getExtSDCardPath(Context mContext,boolean is_removable){
        StorageManager storagerManager=(StorageManager) mContext.getSystemService(Context.STORAGE_SERVICE);
        Class<?> storageVolume=null;
        try {
            storageVolume=Class.forName("android.os.storage.StorageVolume");
            Method getVolumeList=storagerManager.getClass().getMethod("getVolumeList");
            Method getPath=storageVolume.getMethod("getPath");
            Method isRemovable=storageVolume.getMethod("isRemovable");
            Object result=getVolumeList.invoke(storagerManager);
            final int length=Array.getLength(result);
            for(int i=0;i<length;i++){
                Object storageVolumeElement=Array.get(result, i);
                String path=(String) getPath.invoke(storageVolumeElement);
                boolean removable=(Boolean) isRemovable.invoke(storageVolumeElement);
                if(is_removable==removable){
                    return path;
                }
            }
        } catch (NoSuchMethodException e1) {
            e1.printStackTrace();
        } catch (IllegalArgumentException e) {
            e.printStackTrace();
        } catch (IllegalAccessException e) {
            e.printStackTrace();
        } catch (InvocationTargetException e) {
            e.printStackTrace();
        }catch (ClassNotFoundException e) {
            e.printStackTrace();
        }   
        return null;
    }
}
```

上面用到的两个方法`getExtSDCardPath()`获取的是外置SD卡根目录的路径，那另外一个方法`getCardPath()` 是因为从Android 4.4 以后google官方出于安全性考虑，锁住程序对于外接记忆卡的完整访问权限 ，app不再对整张SD卡所有目录有完整存取权限，所有app只对SD卡特定目录有完全控制的权限。这个特定的目录就是Android/data/this.getPackageName() (包名)/files，这个包名是指的你当前工程的包名。

**2 获取到路径后写入到SD卡指定目录的代码如下：**

```
package com.example.testsd;

import java.io.File;
import android.app.Activity;
import android.app.AlertDialog;
import android.content.DialogInterface;
import android.content.DialogInterface.OnClickListener;
import android.os.Bundle;
import android.util.Log;
import android.widget.Toast;

public class MainActivity extends Activity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        //创建Android/data/com.example.testsd/files文件夹
        MainActivity.this.getExternalFilesDir(null);

        if(SDMountUtil.sdMounted(MainActivity.this)){
            SDCardPath sd=new SDCardPath(this);
            File file=new File(sd.getCardPath());
            if(!file.exists()){
                file.mkdir();
                Toast.makeText(this, "创建文件夹成功", Toast.LENGTH_SHORT).show();
            }
        }else {
            AlertDialog.Builder builder=new AlertDialog.Builder(MainActivity.this)
            .setTitle("提示")
            .setMessage("请插入SD卡")
            .setIcon(R.drawable.ic_launcher)
            .setPositiveButton("确定", new OnClickListener() {

                @Override
                public void onClick(DialogInterface dialog, int which) {
                    //下载文件
                    Log.d("tag", "确定");
                }
            })
            .setNegativeButton("取消", new OnClickListener() {

                @Override
                public void onClick(DialogInterface dialog, int which) {
                    Log.d("tag", "取消");
                }
            });
            builder.show();
        }

    }
}
```

这里我只实现了一个简单创建文件夹的操作作为示例，并没有实际的去写入文件。   
 对于安卓4.4以上的版本只需要通过以上方法就可以成功写入到外置SD卡了，对于安卓6.0以上的版本需要动态获取权限，有很多博客都详细的解释了这个问题，我这里就不作说明了。<http://blog.csdn.net/caroline_wendy/article/details/50587230>

**注意：**这里的文件夹并不是通过file.mkdir()创建的，而是getExternalFilesDir()这个方法创建的目录，任何应用私有的文件的都应该被放置在 Context.getExternalFilesDir返回的目录下，在应用被卸载的时候，这个目录下的文件也会被删除。这个条件只成立在android 4.4 以上的版本。

1. 额外需要说明的是安卓4.4 的版本，对于通过getExternalFilesDir()创建目录写入外置SD卡是不成功的。这个是不是只针对于部分机型，由于时间问题，我并没有做相关的测试，我这里只把我测试所有的机器遇到的问题作出说明。并且是我没有找到办法以代码控制的方式去解决这个问题。   
    最后找到的解决办法是通过adb 命令修改机器系统内部的platform.xml文件下的权限，操作方法如下:
2. 通过adb root 命令之后获取到系统目录 system/etc/permissions/platform.xml   
    ![](/images/posts/csdn-72843868-1.png)
3. 通过adb pull 命令取出platform.xml文件到一个本地的路径下。   
    ![这里写图片描述](/images/posts/csdn-72843868-2.png)
4. 用记事本打开之后我们发现文件是这样的   
    ![这里写图片描述](/images/posts/csdn-72843868-3.png)   
    然后我们要做的就是android.permission.WRITE\_EXTERNAL\_STORAGE权限的下面添加

```
   <permission name="android.permission.WRITE_EXTERNAL_STORAGE" >
        <group gid="sdcard_r" />
        <group gid="sdcard_rw" />
        <group gid="media_rw" />
    </permission>
```

需要注意的是添加的`<group gid = "media_rw" />`需要和上面的两个对齐。完成之后保存。

5 . 通过adb push 将修改后的文件push到机器里面   
 ![这里写图片描述](/images/posts/csdn-72843868-4.png)

这样我们就完成了对外置SD卡写入权限的修改，然后再通过上面的方法就可以实现外置SD卡的写入操作了。
