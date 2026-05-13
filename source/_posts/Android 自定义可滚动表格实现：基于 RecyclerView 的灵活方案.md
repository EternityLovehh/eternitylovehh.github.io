---
title: Android 自定义可滚动表格实现：基于 RecyclerView 的灵活方案
date: 2025-07-17 20:58:19
categories:
  - android
tags:
  - android
  - kotlin
---
在 Android 开发中，表格展示是常见需求，但原生控件往往难以满足复杂场景（如固定行列、滚动同步、灵活布局等）。本文将基于 RecyclerView 实现一个可横向 / 纵向滚动、支持固定首行首列的自定义表格，并解析核心实现思路。

## 需求背景与方案设计

- 支持大量数据展示（需滚动）
- 首行（表头）和首列固定，内容区域可滚动
- 横向滚动时，所有行同步滚动（避免表头与内容错位）
- 可自定义单元格布局和数据绑定（灵活适配不同场景）

## 核心设计思路

原生 RecyclerView 本身不支持 “固定行列 + 滚动同步”，因此我们采用 “多 RecyclerView 组合” 方案：

- 一个纵向 RecyclerView（recycler\_content\_list）：承载表格内容行，每行是一个横向 RecyclerView
- 一个横向 RecyclerView（recycler\_header\_list）：承载表头（首行），与内容行横向滚动同步
- 固定首列：单独通过视图添加（不依赖横向 RecyclerView），避免被滚动覆盖
- 滚动同步：监听所有横向 RecyclerView 的滚动事件，强制同步位置

## 核心类结构解析

| 类名 | 作用 |
| --- | --- |
| CustomScrollablePanel | 表格容器，初始化视图和核心逻辑 |
| PanelAdapter | 数据接口，定义表格数据和视图规则 |
| PanelLineAdapter | 内容行适配器，管理每行横向 RecyclerView |
| PanelLineItemAdapter | 单元格适配器，处理单个单元格的视图绑定 |

**1. 容器类：CustomScrollablePanel**  
作为表格的 “外壳”，负责初始化布局、绑定适配器、管理滚动容器，核心代码解析如下：

```
class CustomScrollablePanel @JvmOverloads constructor(
    context: Context, attrs: AttributeSet? = null, defStyleAttr: Int = 0
) : FrameLayout(context, attrs, defStyleAttr) {
    // 核心视图：内容行容器（纵向RecyclerView）和表头（横向RecyclerView）
    private lateinit var recycler_content_list: RecyclerView
    private lateinit var recycler_header_list: RecyclerView
    // 适配器引用
    private var panelLineAdapter: PanelLineAdapter? = null
    private var panelAdapter: PanelAdapter? = null

    init {
        initView() // 初始化视图
    }

    private fun initView() {
        // 加载布局（包含两个RecyclerView和首列容器）
        LayoutInflater.from(context).inflate(R.layout.view_scrollable_panel, this, true)
        // 内容行纵向布局管理器（禁用纵向滚动，避免与外层滚动冲突）
        val mLinearLayoutManager = object : LinearLayoutManager(context) {
            override fun canScrollVertically(): Boolean = false
        }
        recycler_content_list.layoutManager = mLinearLayoutManager
        // 表头横向布局管理器
        recycler_header_list.layoutManager = LinearLayoutManager(context, LinearLayoutManager.HORIZONTAL, false)
        
        // 初始化适配器（关联内容行和表头，实现滚动同步）
        panelAdapter?.let {
            panelLineAdapter = PanelLineAdapter(it, recycler_content_list, recycler_header_list)
            recycler_content_list.adapter = panelLineAdapter
        }
    }

    // 设置适配器（外部调用入口）
    fun setPanelAdapter(panelAdapter: PanelAdapter?) {
        this.panelAdapter = panelAdapter
        // 初始化或更新内容适配器
        if (panelLineAdapter == null) {
            panelLineAdapter = PanelLineAdapter(panelAdapter, recycler_content_list, recycler_header_list)
            recycler_content_list.adapter = panelLineAdapter
        } else {
            panelLineAdapter?.setPanelAdapter(panelAdapter)
        }
    }
}
```

```
<?xml version="1.0" encoding="utf-8"?>

<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:orientation="vertical"
    android:paddingBottom="0.5dp"
    android:paddingRight="0.5dp"
    android:paddingLeft="0.5dp">

    <LinearLayout
        android:layout_width="match_parent"
        android:layout_height="wrap_content">

        <FrameLayout
            android:id="@+id/first_item"
            android:layout_width="wrap_content"
            android:layout_height="match_parent" />

        <androidx.recyclerview.widget.RecyclerView
            android:id="@+id/recycler_header_list"
            android:layout_width="match_parent"
            android:layout_height="wrap_content" />
    </LinearLayout>

    <androidx.recyclerview.widget.RecyclerView
        android:id="@+id/recycler_content_list"
        android:layout_width="match_parent"
        android:layout_height="match_parent" />
</LinearLayout>
```

- 禁用内容纵向 RecyclerView 的滚动（canScrollVertically()返回 false），避免与外层容器滚动冲突
- 通过setPanelAdapter暴露外部接口，由外部决定表格数据和样式
- 单独处理首列第一个单元格（setUpFirstItemView），确保固定显示

**2. 数据接口：PanelAdapter**  
作为 “数据与视图的桥梁”，定义表格的核心规则（行数、列数、单元格视图），由外部实现具体逻辑：

```
abstract class PanelAdapter {
    // 表格行数（需外部实现）
    abstract val rowCount: Int
    // 表格列数（需外部实现）
    abstract val columnCount: Int

    // 单元格视图类型（可选重写，用于多布局）
    open fun getItemViewType(row: Int, column: Int): Int = 0

    // 绑定单元格数据（需外部实现：给指定行列的单元格设置数据）
    abstract fun onBindViewHolder(holder: RecyclerView.ViewHolder?, row: Int, column: Int)

    // 创建单元格视图（需外部实现：定义单元格的布局）
    abstract fun onCreateViewHolder(parent: ViewGroup?, viewType: Int): RecyclerView.ViewHolder
}
```

使用时只需继承 PanelAdapter，实现这几个方法即可定义表格的 “数据结构” 和 “外观”，极大提高灵活性。

**3. 内容行管理：PanelLineAdapter**

这是实现 “滚动同步” 和 “行管理” 的核心类，负责：

管理内容区域的每行横向 RecyclerView  
监听滚动事件，同步所有横向 RecyclerView 的位置  
固定首列（每行第一个单元格单独添加）  
滚动同步核心实现

```
private fun initRecyclerView(recyclerView: RecyclerView?) {
    // 监听当前RecyclerView的滚动事件
    recyclerView?.addOnScrollListener(object : RecyclerView.OnScrollListener() {
        override fun onScrolled(recyclerView: RecyclerView, dx: Int, dy: Int) {
            super.onScrolled(recyclerView, dx, dy)
            val linearLayoutManager = recyclerView.layoutManager as LinearLayoutManager?
            linearLayoutManager?.let {
                // 获取当前第一个可见item的位置和偏移量
                val firstPos = it.findFirstVisibleItemPosition()
                val firstVisibleItem = it.getChildAt(0)
                if (firstVisibleItem != null) {
                    val firstRight = it.getDecoratedRight(firstVisibleItem) // 偏移量
                    // 同步所有横向RecyclerView的滚动位置
                    for (rv in observerList) {
                        if (recyclerView !== rv) { // 排除当前滚动的RV
                            rv?.layoutManager?.let { layoutManager ->
                                (layoutManager as LinearLayoutManager).scrollToPositionWithOffset(
                                    firstPos + 1, 
                                    firstRight
                                )
                            }
                        }
                    }
                }
            }
        }
    })
}
```

```
<?xml version="1.0" encoding="utf-8"?>

<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:orientation="vertical"
    android:paddingBottom="0.5dp"
    android:paddingRight="0.5dp"
    android:paddingLeft="0.5dp">

    <LinearLayout
        android:layout_width="match_parent"
        android:layout_height="wrap_content">

        <FrameLayout
            android:id="@+id/first_item"
            android:layout_width="wrap_content"
            android:layout_height="match_parent" />

        <androidx.recyclerview.widget.RecyclerView
            android:id="@+id/recycler_header_list"
            android:layout_width="match_parent"
            android:layout_height="wrap_content" />
    </LinearLayout>

    <androidx.recyclerview.widget.RecyclerView
        android:id="@+id/recycler_content_list"
        android:layout_width="match_parent"
        android:layout_height="match_parent" />
</LinearLayout>
```

**滚动同步原理：**

- 用observerList收集所有横向 RecyclerView（表头 + 所有内容行）
- 当任意一个横向 RV 滚动时，获取其第一个可见 item 的位置和偏移量
- 遍历observerList，强制其他所有横向 RV 滚动到相同位置 行视图绑定
- 每行包含 “首列固定单元格” 和 “横向内容 RV”，在onBindViewHolder中初始化：

```
override fun onBindViewHolder(holder: ViewHolder, position: Int) {
    // 初始化当前行的横向内容RV适配器
    var lineItemAdapter = holder.recyclerView.adapter as PanelLineItemAdapter?
    if (lineItemAdapter == null) {
        lineItemAdapter = PanelLineItemAdapter(position + 1, panelAdapter)
        holder.recyclerView.adapter = lineItemAdapter
    } else {
        lineItemAdapter.setRow(position + 1)
        lineItemAdapter.notifyDataSetChanged()
    }

    // 初始化首列固定单元格（当前行第0列）
    if (holder.firstColumnItemVH == null) {
        val viewHolder = panelAdapter?.onCreateViewHolder(holder.firstColumnItemView, 
            panelAdapter.getItemViewType(position + 1, 0)
        )
        holder.firstColumnItemVH = viewHolder
        panelAdapter?.onBindViewHolder(viewHolder, position + 1, 0)
        holder.firstColumnItemView.addView(viewHolder?.itemView)
    }
}
```

**4. 单元格适配器：PanelLineItemAdapter**

负责单个单元格的视图创建和数据绑定，是连接PanelAdapter与具体单元格的桥梁：

kotlin  
class PanelLineItemAdapter (  
private var row: Int, // 当前行  
private val panelAdapter: PanelAdapter?  
) : RecyclerView.Adapter<RecyclerView.ViewHolder>() {  
override fun getItemCount(): Int {  
return panelAdapter?.columnCount?.minus(1) ?: 0 // 列数-1（排除首列）  
}

```
override fun onBindViewHolder(holder: RecyclerView.ViewHolder, position: Int) {
    // 绑定数据：当前行 = row，当前列 = position + 1（排除首列）
    panelAdapter?.onBindViewHolder(holder, row, position + 1)
}
```

}

**注意**：position + 1是因为首列已单独处理，这里只处理从第 1 列开始的内容列。  
**使用示例**  
只需三步即可实现自定义表格：

1. 定义单元格布局（如item\_table\_cell.xml）
2. 实现 PanelAdapter（定义数据和视图）
3. 在布局中使用 ScrollablePanel 并设置适配器

### 步骤 1：实现 PanelAdapter

```
class MyTableAdapter(private val itemWidth: Int, private val formDetail: Boolean = true) : PanelAdapter() {

    companion object {
        private const val TITLE_TYPE = 4
        private const val ROOM_TYPE = 0
        private const val DATE_TYPE = 1
        private const val ORDER_TYPE = 2
    }

    private var mColumnInfoList: List<String?> = arrayListOf()
    private var mRowInfoList: List<String?> = arrayListOf()
    private var mContentInfoList: ArrayList<ArrayList<String>?> = arrayListOf()
    private var mTitleList: List<String?> = arrayListOf()

    override val rowCount: Int
        get() = mColumnInfoList.size + 1
    override val columnCount: Int
        get() = mRowInfoList.size + 1

    override fun getItemViewType(row: Int, column: Int): Int {
        if (column == 0 && row == 0) {
            return TITLE_TYPE
        }
        if (column == 0) {
            return ROOM_TYPE
        }
        return if (row == 0) {
            DATE_TYPE
        } else ORDER_TYPE
    }

    override fun onBindViewHolder(holder: RecyclerView.ViewHolder?, row: Int, column: Int) {
        when (getItemViewType(row, column)) {
            DATE_TYPE -> setRowView(column, holder as RowViewHolder)
            ROOM_TYPE -> setColumnView(row, holder as ColumnViewHolder)
            TITLE_TYPE -> setTitltView(holder as TitleViewHolder)
            else -> setContentView(row, column, holder as ContentViewHolder)
        }
    }

    override fun onCreateViewHolder(parent: ViewGroup?, viewType: Int): RecyclerView.ViewHolder {
        when (viewType) {
            DATE_TYPE -> return RowViewHolder(
                LayoutInflater.from(parent?.context)
                    .inflate(R.layout.item_first_row, parent, false)
            )
            ROOM_TYPE -> return ColumnViewHolder(
                LayoutInflater.from(parent?.context)
                    .inflate(R.layout.item_first_column, parent, false)
            )
            TITLE_TYPE -> return TitleViewHolder(
                LayoutInflater.from(parent?.context)
                    .inflate(R.layout.item_table_title, parent, false)
            )
            else -> {
                return ContentViewHolder(
                    LayoutInflater.from(parent?.context)
                        .inflate(R.layout.item_table_content, parent, false)
                )
            }
        }
    }


    private fun setRowView(pos: Int, viewHolder: RowViewHolder) {
        val dateInfo = mRowInfoList[pos - 1]
        if (dateInfo != null && pos > 0) {
            viewHolder.tvRowTitle.text = dateInfo
        }
        viewHolder.itemView.layoutParams.apply {
            width = if (mRowInfoList.size in 1..4) {
                (ScreenUtils.getScreenWidth() - itemWidth) / (mRowInfoList.size)
            } else {
                ((ScreenUtils.getScreenWidth() - SizeUtils.dp2px(40f)) / 5.2f).toInt()
            }

        }
    }

    private fun setColumnView(pos: Int, viewHolder: ColumnViewHolder) {
        val roomInfo = mColumnInfoList[pos - 1]
        if (roomInfo != null && pos > 0) {
            viewHolder.tvColumnTitle.text = roomInfo
        }
        viewHolder.itemView.layoutParams.apply {
            width = if (mRowInfoList.size in 1..4) {
                (ScreenUtils.getScreenWidth() - itemWidth) / (mRowInfoList.size)
            } else {
                ((ScreenUtils.getScreenWidth() - SizeUtils.dp2px(40f)) / 5.2f).toInt()
            }

        }
        if (pos == mColumnInfoList.size) {
            viewHolder.itemView.setBackgroundResource(R.drawable.bg_first_column_corner)
        }
    }

    private fun setContentView(row: Int, column: Int, viewHolder: ContentViewHolder) {
        val orderInfo = mContentInfoList[row - 1]?.get(column - 1)
        if (orderInfo != null) {
            viewHolder.tvContentTitle.text = orderInfo

            viewHolder.itemView.layoutParams.apply {
                width = if (mRowInfoList.size in 1..4) {
                    (ScreenUtils.getScreenWidth() - itemWidth) / (mRowInfoList.size)
                } else {
                    ((ScreenUtils.getScreenWidth() - SizeUtils.dp2px(40f)) / 5.2f).toInt()
                }

            }
            when {
                row == mColumnInfoList.size && column != mRowInfoList.size -> {
                    viewHolder.itemView.background = null
                    viewHolder.viewLine.isVisible = true
                }
                row == mColumnInfoList.size && column == mRowInfoList.size -> {
                    viewHolder.viewLine.isVisible = false
                }
                column == mRowInfoList.size -> {
                    viewHolder.itemView.setBackgroundResource(R.drawable.bg_last_column_border)
                    viewHolder.viewLine.isVisible = false
                }
                else -> {
                    viewHolder.itemView.setBackgroundResource(R.drawable.bg_table_content_border)
                    viewHolder.viewLine.isVisible = true
                }
            }
        }
    }

    private fun setTitltView(viewHolder: TitleViewHolder) {
        if (mTitleList.isNotNullAndEmpty()) {
            if (mTitleList.size > 1) {
                viewHolder.clMoreTitle.isVisible = true
                viewHolder.titleTextView.isVisible = false
                viewHolder.tvLeftTitle.text = mTitleList[1]
                viewHolder.tvRightTitle.text = mTitleList[0]
                viewHolder.ivDiagonalLine.isVisible = true
            } else {
                viewHolder.ivDiagonalLine.isVisible = false
                viewHolder.clMoreTitle.isVisible = false
                viewHolder.titleTextView.isVisible = true
                viewHolder.titleTextView.text = mTitleList[0]
            }
            viewHolder.itemView.layoutParams.apply {
                width = if (mRowInfoList.size in 1..4) {
                    (ScreenUtils.getScreenWidth() - itemWidth) / (mRowInfoList.size)
                } else {
                    ((ScreenUtils.getScreenWidth() - SizeUtils.dp2px(40f)) / 5.2f).toInt()
                }
            }
        }
    }

    class RowViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        var tvRowTitle: TextView = itemView.findViewById(R.id.tv_row_title)
    }

    private class ColumnViewHolder(view: View) : RecyclerView.ViewHolder(view) {
        var tvColumnTitle: TextView = view.findViewById(R.id.tv_column_title)
    }

    private class ContentViewHolder(view: View) : RecyclerView.ViewHolder(view) {
        var tvContentTitle: TextView = view.findViewById(R.id.tv_content_title)
        var viewLine: View = view.findViewById(R.id.view_line)
    }

    private class TitleViewHolder(view: View) : RecyclerView.ViewHolder(view) {
        val ivDiagonalLine: ImageView = view.findViewById(R.id.iv_diagonal_line)
        var titleTextView: TextView = view.findViewById(R.id.tv_title)
        var clMoreTitle: ConstraintLayout = view.findViewById(R.id.cl_more_title)
        var tvLeftTitle: TextView = view.findViewById(R.id.tv_left_title)
        var tvRightTitle: TextView = view.findViewById(R.id.tv_right_title)
    }

    fun setColumnInfoList(mColumnInfoList: ArrayList<String?>) {
        this.mColumnInfoList = mColumnInfoList
    }

    fun setRowInfoList(mRowInfoList: ArrayList<String?>) {
        this.mRowInfoList = mRowInfoList
    }

    fun setContentInfoList(mContentInfoList: ArrayList<ArrayList<String>?>) {
        this.mContentInfoList = mContentInfoList
    }

    fun setTitleList(titleList: ArrayList<String?>) {
        this.mTitleList = titleList
    }


}
```

### 步骤 2：在 Activity 中使用

```
class TableActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_table)
        val scrollablePanel = findViewById<ScrollablePanel>(R.id.scrollable_panel)
        scrollablePanelAdapter.setTitleList(titleInfoList)
        scrollablePanelAdapter.setColumnInfoList(columnInfoList)
        scrollablePanelAdapter.setRowInfoList(rowInfoList)
        scrollablePanelAdapter.setContentInfoList(contentInfoList)
        scrollablePanel.setPanelAdapter(MyTableAdapter()) // 设置适配器
    }
}
```

**实现效果:**  
![在这里插入图片描述](/images/posts/csdn-149429425-1.png)

## 优势与扩展建议

### 方案优势

1. 灵活性高：通过PanelAdapter完全自定义单元格布局和数据
2. 滚动流畅：基于 RecyclerView 复用机制，支持大量数据
3. 同步准确：滚动同步逻辑确保表头与内容无错位
4. 结构清晰：分工明确的类设计，便于维护

### 扩展建议

1. 添加点击事件：在PanelAdapter中增加onItemClick接口 支持列宽自适应：通过测量单元格宽度动态设置RecyclerView 宽度
2. 优化性能：对observerList的遍历可加入防抖处理，避免频繁触发
3. 支持合并单元格：在PanelAdapter中增加合并规则，在绑定视图时处理

## 总结

本文实现的自定义表格通过 “多 RecyclerView 组合 + 滚动同步” 方案，解决了 Android 原生控件难以实现 “固定行列 + 灵活布局” 的问题。核心在于通过PanelLineAdapter管理滚动同步，通过PanelAdapter暴露灵活接口，既满足了功能需求，又保留了扩展空间。

如果你需要实现复杂表格（如数据报表、订单明细），这个方案可以作为基础框架，根据实际需求扩展即可。
