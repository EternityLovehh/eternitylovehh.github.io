title: HashMap 原理
---
HashMap 实际上是数组+链表组合构成的数据结构
![在这里插入图片描述](E:\github\myblog\source\images\20190416160043844.png)

**hash函数的原理**
    java中任何对象都有hash值，计算key的hash值， 对key的hashcode进行移位，异或运算（相同为0，不同为1），然后通过hash函数计算的index找到数组的位置（求模运算 hash % length, hash&length - 1）。流程如下：
**![加粗样式](E:\github\myblog\source\images\20190416161656243.png)
hash函数作用是为了保证最终获取的存储位置尽量分布均匀。

**put方法原理**
     由key得到hash值，根据hash值，得到数组的下标index，找到对应的entry, 判断table[i] 和 entry 的key值和hash值是否相等，相等就用put传入的value替换原value。如果没有找到entry，就创建一个新节点entry  (创建节点，new Entry(key, value, hash, entry)，这里是因为有可能table[i] 下面已经存在节点或者是链表，这个 时候，创建一个新的entry，将entry的next指针指向第一个节点，并且将新建的节点entry作为table[i]的第一个节点table[i] = new Entry(key, value, hash, entry)。put方法源码实现如下：

```
public V put(K key, V value) {
        //如果table数组为空数组{}，进行数组填充（为table分配实际内存空间），入参为threshold，此时threshold为initialCapacity 默认是1<<4(24=16)
        if (table == EMPTY_TABLE) {
            inflateTable(threshold);
        }
       //如果key为null，存储位置为table[0]或table[0]的冲突链上
        if (key == null)
            return putForNullKey(value);
        int hash = hash(key);//对key的hashcode进一步计算，确保散列均匀
        int i = indexFor(hash, table.length);//获取在table中的实际位置
        for (Entry<K,V> e = table[i]; e != null; e = e.next) {
        //如果该对应数据已存在，执行覆盖操作。用新value替换旧value，并返回旧value
            Object k;
            if (e.hash == hash && ((k = e.key) == key || key.equals(k))) {
                V oldValue = e.value;
                e.value = value;
                e.recordAccess(this);
                return oldValue;
            }
        }
        modCount++;//保证并发访问时，若HashMap内部结构发生变化，快速响应失败
        addEntry(hash, key, value, i);//新增一个entry
        return null;
    }
```

java8之前使用头插法，在java8之后，改用为尾部插入法，为啥要改为尾部插入呢？主要是使用头插方式，可能会导致扩容转移后 前后链表顺序倒置，产生死循环。而使用尾插方式，扩容转移前后链表的顺序不变。

**get原理**
key得到hash值，根据hash值，得到数组的下标index,然后遍历对应的链表，比较table[i]与链表的节点hash值是否相等，key是否相等，相等返回链表的值。

```
public V get(Object key) {
　　　　 //如果key为null,则直接去table[0]处去检索即可。
        if (key == null)
            return getForNullKey();
        Entry<K,V> entry = getEntry(key);
        return null == entry ? null : entry.getValue();
 }
```
get方法通过key值返回对应value，如果key为null，直接去table[0]处检索。getEntry方法：
```
final Entry<K,V> getEntry(Object key) {
            
        if (size == 0) {
            return null;
        }
        //通过key的hashcode值计算hash值
        int hash = (key == null) ? 0 : hash(key);
        //indexFor (hash&length-1) 获取最终数组索引，然后遍历链表，通过equals方法比对找出对应记录
        for (Entry<K,V> e = table[indexFor(hash, table.length)];
             e != null;
             e = e.next) {
            Object k;
            if (e.hash == hash && 
                ((k = e.key) == key || (key != null && key.equals(k))))
                return e;
        }
        return null;
    }
```

**扩容**

​      HashMap的扩容机制,  首先我们知道数组的容量是有限的，在数据多次插入的情况下，到达原阈值，就会进行扩容。也就是resize。那在什么时候开始resize呢？有两个主要因素：

1. HashMap当前的长度length
2. 负载因子，默认值为0.75f

当put进去的index > length * 0.75f的时候，就要resize了。

那么怎么进行扩容呢

首先创建一个新的Entry空数组，长度是原来的2倍。然后遍历原先的数组，把所有的Entry重新rehash到新数组，这里要重新hash而不是直接复制，是因为长度扩大之后，hash规则也改变了（jdk1.7）。在jdk 1.8 里面 直接通过 (n - 1) & hash获得index的值。

**hash碰撞**
不同对象算出来index相同，也就是说，当我们对某个元素进行哈希运算，得到一个存储地址，然后要进行插入的时候，发现已经被其他元素占用了
解决方法：jdk 1.7 单向链表
jdk 1.8 红黑树

