---
title: 自定义 AqiColorView：优雅实现空气质量指数可视化展示
date: 2025-07-11 13:40:49
tags:
  - android
  - kotlin
---
Android 仿IOS 天气 AQI彩色进度条实现  
![在这首先z里插入图片描述](/images/posts/csdn-149269671-1.png)

### 一. 需求分析

空气质量指数（AQI）通常分为 6 个等级：

- 0-50 绿色
- 51-100 黄色
- 101-150 橙色
- 151-200 红色
- 201-300 紫色
- 301-500 棕色

我们需要实现：

- 多色块渐变背景
- 动态圆点指示器
- 圆角矩形边框
- 可配置颜色数组
- 响应式布局适配

### 二. 关键技术实现

1. 支持自定义属性配置

```
<declare-styleable name="AqiColorView">
    <attr name="aqi_background_color" format="color" />
    <attr name="aqi_circle_radius" format="dimension" />
    <attr name="aqi_roundrect_radius" format="dimension" />
    <attr name="aqi_multi_color" format="boolean" />
    <attr name="aqi_min_value" format="float" />
    <attr name="aqi_max_value" format="float" />
</declare-styleable>
```

2. 渐变色生成

```
 private fun initGradientShader() {
        mGradientShader = LinearGradient(
            0f, 0f, width.toFloat(), 0f, colorArray, null, Shader.TileMode.CLAMP
        )
    }
```

3. 颜色分段与多色设计

AQI 的 6 个等级对应 6 种颜色（绿色→黄色→橙色→红色→紫色→棕色），colorArray 数组存储了这些颜色值。多色绘制的核心逻辑在 drawMultiColor 方法中：

```
 private fun drawMultiColor(canvas: Canvas) {
        val segmentWidth = width.toFloat() / colorArray.size
        mStepGradient = width / (mMaxValue - mMinValue)
        //设置渐变色区域
        mPaint.setShader(mGradientShader)
        colorArray.forEachIndexed { index, _ ->
            mTempRectF.set((index * segmentWidth - 1), 0f, (index + 1) * segmentWidth, height.toFloat())
            mPath.apply {
                reset()
                when (index) {
                    0 -> {
                        mPath.addRoundRect(mTempRectF, mLeftRadiusArray, Path.Direction.CW)
                    }
                    colorArray.size - 1 -> mPath.addRoundRect(mTempRectF, mRightRadiusArray, Path.Direction.CW)
                    else -> addRect(mTempRectF, Path.Direction.CW)
                }
            }
            canvas.drawPath(mPath, mPaint)
        }
    }
```

- 分段宽度平均分配（width / colorArray.size），确保 6 种颜色各占相同比例；
- 首尾段通过 mLeftRadiusArray 和 mRightRadiusArray 处理圆角（8 个元素的数组对应 4 个角的 x/y  
  半径）；
- 使用 Path 绘制不同形状的区域，避免多次创建 Path 对象（复用 mPath）；
- 复用 mTempRectF 减少 RectF 对象的频繁创建，优化内存占用。

4. 当前值指示圆点计算  
   为了直观标记当前 AQI 值的位置，View 会绘制一个指示圆点，其位置通过 getCenterCircleX 计算：

```
  /**
     * 当前温度 == 最低温度 || 当前温度 == 最高温度，圆点位置特殊计算，
     * 如果每个刻度的宽度不足圆点的半径，可能会出现x值偏差，导致圆点显示位置异常
     */
    private fun getCenterCircleX(): Float {
        val segmentWidth = width / (mMaxValue - mMinValue + 1)
        return when (mValue) {
            mMinValue -> {
                mCircleRadius
            }
            mMaxValue -> {
                width - mCircleRadius
            }
            else -> {
                (mValue - mMinValue) * segmentWidth + segmentWidth / 2f
            }
        }
    }
```

- 当 mValue 为最小值时，圆点左边缘不超出 View 范围（mCircleRadius）；
- 当 mValue 为最大值时，圆点右边缘不超出 View 范围（width - mCircleRadius）；
- 中间值通过比例计算位置，确保与对应颜色段对齐。

5. 多模式支持  
   View 通过 mAqiMultiColor 变量支持两种显示模式：

- 多色模式（mAqiMultiColor = true）：通过 drawMultiColor 绘制 6 色分段，适合展示完整的 AQI  
  等级范围；
- 单色模式（mAqiMultiColor = false）：通过 drawTemperatureRect  
  绘制单色背景（带透明度），适合简化场景。

完整的代码实现如下：

```
class AqiColorView @JvmOverloads constructor(
    context: Context, attrs: AttributeSet? = null, defStyleAttr: Int = 0
) : View(context, attrs, defStyleAttr) {

    companion object {
        private const val TAG = "AqiColorView"
    }

    private var mValue = 0f

    private var mPaint = Paint().apply {
        isAntiAlias = true
        style = Paint.Style.FILL_AND_STROKE
    }

    private var mPath = Path()
    private var mGradientShader: Shader? = null
    //  复用 RectF 对象
    private val mTempRectF = RectF()
    // AQI 分段颜色值
    private val colorArray = intArrayOf(
        context.getColor(R.color.aqi_green),
        context.getColor(R.color.aqi_yellow),
        context.getColor(R.color.aqi_orange),
        context.getColor(R.color.aqi_red),
        context.getColor(R.color.aqi_purple),
        context.getColor(R.color.aqi_brown_color),
    )

    private var mApiBackGroundColor = Color.WHITE
    private var mCircleRadius: Float = 0f
    private var mAqiMultiColor: Boolean = false
    private var mStepGradient: Float = 0f
    private var mRoundRectRadius: Float = 0f
    private var mMinValue: Float = 0f
    private var mMaxValue: Float = 0f
    private val mLeftRadiusArray by lazy {
        floatArrayOf(mRoundRectRadius, mRoundRectRadius, 0f, 0f, 0f, 0f, mRoundRectRadius, mRoundRectRadius)
    }
    private val mRightRadiusArray by lazy {
        floatArrayOf(0f, 0f, mRoundRectRadius, mRoundRectRadius, mRoundRectRadius, mRoundRectRadius, 0f, 0f)
    }
    private val mAqiCircleColor by lazy {
        MaterialColors.getColor(this, com.google.android.material.R.attr.colorOnPrimaryContainer)
    }

    init {
        val a = context.obtainStyledAttributes(attrs, R.styleable.AqiColorView, defStyleAttr, 0)
        mApiBackGroundColor = a.getColor(R.styleable.AqiColorView_aqi_background_color, Color.WHITE)
        mCircleRadius = a.getDimensionPixelSize(R.styleable.AqiColorView_aqi_circle_radius, 0).toFloat()
        mRoundRectRadius = a.getDimensionPixelSize(R.styleable.AqiColorView_aqi_roundrect_radius, 0).toFloat()
        mAqiMultiColor = a.getBoolean(R.styleable.AqiColorView_aqi_multi_color, false)
        mMinValue = a.getFloat(R.styleable.AqiColorView_aqi_min_value, 0f)
        mMaxValue = a.getFloat(R.styleable.AqiColorView_aqi_max_value, 0f)
        a.recycle()
        setLayerType(LAYER_TYPE_HARDWARE, null)
        setWillNotDraw(false)
    }

    fun setCurrentValue(value: Float) {
        mValue = value
        postInvalidateOnAnimation()
    }

    fun setMinValue(value: Float) {
        mMinValue = value
    }

    fun setMaxValue(value: Float) {
        mMaxValue = value
    }

    private fun initGradientShader() {
        mGradientShader = LinearGradient(
            0f, 0f, width.toFloat(), 0f, colorArray, null, Shader.TileMode.CLAMP
        )
    }

    override fun onSizeChanged(w: Int, h: Int, oldw: Int, oldh: Int) {
        super.onSizeChanged(w, h, oldw, oldh)
        if (w > 0) initGradientShader()
    }

    override fun draw(canvas: Canvas) {
        super.draw(canvas)
        if (mAqiMultiColor) {
            drawMultiColor(canvas)
            drawAqiCircle(canvas)
        } else {
            drawTemperatureRect(canvas)
            drawTemperatureCircle(canvas)
        }
    }

    private fun drawTemperatureRect(canvas: Canvas) {
        mTempRectF.set(0f, 0f, width.toFloat(), height.toFloat())
        mPaint.setShader(null)
        mPaint.color = mApiBackGroundColor
        mPaint.alpha = 40
        canvas.drawRoundRect(mTempRectF, mRoundRectRadius, mRoundRectRadius, mPaint)
    }

    private fun drawMultiColor(canvas: Canvas) {
        val segmentWidth = width.toFloat() / colorArray.size
        mStepGradient = width / (mMaxValue - mMinValue)
        //设置渐变色区域
        mPaint.setShader(mGradientShader)
        colorArray.forEachIndexed { index, _ ->
            mTempRectF.set((index * segmentWidth - 1), 0f, (index + 1) * segmentWidth, height.toFloat())
            mPath.apply {
                reset()
                when (index) {
                    0 -> {
                        mPath.addRoundRect(mTempRectF, mLeftRadiusArray, Path.Direction.CW)
                    }
                    colorArray.size - 1 -> mPath.addRoundRect(mTempRectF, mRightRadiusArray, Path.Direction.CW)
                    else -> addRect(mTempRectF, Path.Direction.CW)
                }
            }
            canvas.drawPath(mPath, mPaint)
        }
    }

    private fun drawAqiCircle(canvas: Canvas) {
        //白色内圆
        mPaint.setShader(null)
        mPaint.setColor(mAqiCircleColor)
        canvas.drawCircle(getCenterCircleX(), height.toFloat() / 2, mCircleRadius, mPaint);
    }

    private fun drawTemperatureCircle(canvas: Canvas) {
        //白色内圆
        mPaint.setShader(null)
        mPaint.setColor(mAqiCircleColor)
        canvas.drawCircle(getCenterCircleX(), height.toFloat() / 2, mCircleRadius, mPaint)
    }

    /**
     * 当前温度 == 最低温度 || 当前温度 == 最高温度，圆点位置特殊计算，
     * 如果每个刻度的宽度不足圆点的半径，可能会出现x值偏差，导致圆点显示位置异常
     */
    private fun getCenterCircleX(): Float {
        val segmentWidth = width / (mMaxValue - mMinValue + 1)
        return when (mValue) {
            mMinValue -> {
                mCircleRadius
            }
            mMaxValue -> {
                width - mCircleRadius
            }
            else -> {
                (mValue - mMinValue) * segmentWidth + segmentWidth / 2f
            }
        }
    }

}
```

### 三. 使用方法

在xml中引入刚刚实现的自定义view, 配置相关的参数

```
 <com.nextev.weather.view.AqiColorView
            android:id="@+id/seek_range_temperature"
            android:layout_width="@dimen/fy_size_160px"
            android:layout_height="@dimen/fy_size_16px"
            android:layout_marginEnd="@dimen/fy_size_48px"
            app:aqi_background_color="?android:textColorPrimaryDisableOnly"
            app:aqi_circle_radius="@dimen/fy_size_6px"
            app:aqi_multi_color="false"
            app:aqi_roundrect_radius="@dimen/fy_size_12px"
            app:layout_constraintEnd_toEndOf="parent"
            app:layout_constraintTop_toTopOf="@id/temperature_range"
            app:layout_constraintBottom_toBottomOf="@id/temperature_range"/>
```

代码中传入实际返回的aqi 值，和定义的最大最小值。

```
 seekRangeUltraviolet.setMinValue(Constants.NUM0.toFloat())
 seekRangeUltraviolet.setMaxValue(Constants.NUM500.toFloat())
 seekRangeUltraviolet.setCurrentValue(it.city_air.aqi.toFloat())
```
