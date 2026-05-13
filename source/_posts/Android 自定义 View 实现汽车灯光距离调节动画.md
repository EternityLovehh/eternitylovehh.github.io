---
title: Android 自定义 View 实现汽车灯光距离调节动画
date: 2025-07-15 17:18:43
categories:
  - android
tags:
  - android
  - 汽车
cover: /images/posts/csdn-149359519-1.png
---
在汽车控制类应用中，灯光距离调节是一个常见的交互场景 —— 用户通过调节滑块或按钮，实时看到前灯光照范围的变化，直观反馈操作效果。本文将基于实际项目代码，详解如何通过自定义 View 实现这一效果，包括光照区域绘制、平滑动画过渡及性能优化等核心技术点。

## 一、功能需求与效果展示

### 需求分析

汽车前灯的光照范围调节需要实现：

- 显示前灯的光照区域（含渐变效果，模拟真实灯光衰减）
- 支持 5 种光照距离（从近到远，光照范围逐渐扩大）
- 切换距离时，光照边缘需平滑动画过渡
- 光照区域需有边框线，增强视觉边界感

### 最终效果

光照区域随调节等级变化，从近到远逐渐扩大，切换时有流畅的动画，光照颜色从光源处向外逐渐变淡（模拟真实灯光衰减）。  
![在这里插入图片描述](/images/posts/csdn-149359519-1.png)

## 二、核心实现：自定义 CarHeadLightView

自定义 View 是实现这一效果的核心，需处理形状绘制、渐变效果、属性动画三大核心问题。

### 2.1 基础结构与初始化

自定义 View 的基础结构包括属性定义、画笔初始化、关键数据准备（如光照区域的顶点坐标）：

```
// 光照区域画笔（填充渐变）
    private val mLightPaint by lazyPaint {
        style = Paint.Style.FILL
        isAntiAlias = true // 抗锯齿，避免边缘毛刺
    }

    // 边框画笔（边框渐变）
    private val mBorderLinePaint by lazyPaint {
        style = Paint.Style.STROKE
        strokeWidth = 2f // 边框宽度
        isAntiAlias = true
    }

    // 光照区域路径（核心：定义光照的形状）
    private val mPath by lazy { Path() }

    // 光照区域的顶点集合（动态更新，决定光照范围）
    private var mCurrentPoints = mutableListOf<PointF>()

    // 存储5种光照距离对应的顶点坐标（key：等级0-4，value：顶点集合）
    private val mAllPointsArray: SparseArray<List<PointF>> = SparseArray<List<PointF>>().apply {
        put(0, listOf(PointF(1329.6f, 464f), PointF(837.2f, 464f))) // 最近距离
        put(1, listOf(PointF(1314.6f, 464f), PointF(765.3f, 464f)))
        put(2, listOf(PointF(1301.4f, 464f), PointF(678.3f, 464f)))
        put(3, listOf(PointF(1279.2f, 464f), PointF(518.4f, 464f)))
        put(4, listOf(PointF(1258.8f, 464f), PointF(333.9f, 464f))) // 最远距离
    }

    // 固定的光源起点（前灯位置，不随距离变化）
    private val initPoints = listOf(PointF(1228.2f, 226.4f), PointF(1395.4f, 283.4f))

    init {
        // 开启硬件加速，提升绘制性能
        setLayerType(LAYER_TYPE_HARDWARE, null)
        // 初始化光照区域的弧形路径（仅计算一次，缓存结果）
        mArcPathParams = buildArcPath()
    }

    // 懒加载画笔的工具方法
    private inline fun lazyPaint(crossinline block: Paint.() -> Unit): Lazy<Paint> =
        lazy { Paint().apply(block) }
```

- 光照区域由多个顶点定义，其中initPoints是固定的光源位置（前灯所在点），mAllPointsArray存储不同距离对应的终点（光照最远点），通过组合这些点形成完整的光照范围。
- 使用lazy初始化画笔，避免重复创建；通过setLayerType(LAYER\_TYPE\_HARDWARE)开启硬件加速，适合频繁绘制的场景。

## 三、光照区域绘制：Path 与渐变效果

光照区域的视觉效果是核心，需要通过Path构建不规则形状，并结合渐变 shader 模拟灯光衰减。

### 3.1 构建光照区域的路径（Path）

汽车前灯的光照区域通常是 “扇形” 或 “类梯形”，由固定的光源点和可变的终点连接而成，且顶部边缘为弧形（模拟灯光的扩散效果）。

```
override fun onDraw(canvas: Canvas) {
    super.onDraw(canvas)
    if (mCurrentPoints.size < 4) { // 至少需要4个点（2个光源点+2个终点）
        return
    }
    drawLightArea(canvas) // 绘制光照填充区域
    drawBorderLine(canvas) // 绘制边框线
}

/** 绘制光照填充区域 */
private fun drawLightArea(canvas: Canvas) {
    mPath.apply {
        reset()
        // 从第一个光源点开始
        moveTo(mCurrentPoints[0].x, mCurrentPoints[0].y)
        // 绘制顶部弧形边缘（连接两个光源点的弧形）
        val (startAngle, sweepAngle) = mArcPathParams?.first ?: return
        val rect = mArcPathParams?.second ?: return
        arcTo(rect, startAngle, sweepAngle)
        // 连接到第一个终点，再连接到第二个终点，最后闭合路径
        lineTo(mCurrentPoints[2].x, mCurrentPoints[2].y)
        lineTo(mCurrentPoints[3].x, mCurrentPoints[3].y)
        close() // 闭合路径（自动连接回起点）
    }
    // 用带渐变的画笔绘制路径
    canvas.drawPath(mPath, mLightPaint)
}

/** 计算弧形路径的参数（圆心、半径、角度） */
private fun buildArcPath(): Pair<FloatArray, RectF>? {
    // 基于固定光源点计算弧形的圆心、半径、起始角度
    val (centerX, centerY, radius) = calculateArcParams() ?: return null
    val startAngle = calculateStartAngle(centerX, centerY) // 起始角度
    val sweepAngle = calculateSweepAngle(centerX, centerY) // 扫过的角度
    // 弧形所在的矩形（用于arcTo方法）
    val rect = RectF(
        centerX - radius,
        centerY - radius,
        centerX + radius,
        centerY + radius
    )
    return Pair(floatArrayOf(startAngle, sweepAngle), rect)
}

/** 计算弧形的圆心和半径（基于3个点：2个光源点+1个中间点） */
private fun calculateCenterAndRadius(x1: Float, y1: Float, x2: Float, y2: Float, x3: Float, y3: Float): FloatArray {
    // 基于三点求圆的数学公式（计算圆心(xc,yc)和半径）
    val ma = (y2 - y1) / (x2 - x1) // 第一条线的斜率
    val mb = (y3 - y2) / (x3 - x2) // 第二条线的斜率
    // 计算圆心x坐标
    val xc = (ma * mb * (y1 - y3) + mb * (x1 + x2) - ma * (x2 + x3)) / (2 * (mb - ma))
    // 计算圆心y坐标
    val yc = -1 * (xc - (x1 + x2) / 2) / ma + (y1 + y2) / 2
    // 计算半径（圆心到任意一点的距离）
    val radius = sqrt(((x1 - xc) * (x1 - xc) + (y1 - yc) * (y1 - yc)).toDouble()).toFloat()
    return floatArrayOf(xc, yc, radius)
}
```

- 弧形路径通过arcTo绘制，需要先计算弧形的圆心、半径、起始角度和扫过角度。
- 三点求圆公式：通过 2 个光源点和 1 个中间点计算弧形的圆心，确保弧形完美连接两个光源点，形成自然的顶部边缘。

### 3.2 渐变效果：模拟灯光衰减

真实灯光的亮度会随距离衰减（光源处最亮，远处逐渐变暗），通过LinearGradient实现这一效果：

```
/** 更新渐变效果（灯光从亮到暗的衰减） */
private fun updateGradients() {
    // 光照填充区域的渐变（从光源到终点，透明度逐渐降低）
    mLightPaint.shader = createGradient(
        colorArray = intArrayOf(
            ContextCompat.getColor(context, R.color.light_fill_init_color), // 光源处：亮
            ContextCompat.getColor(context, R.color.light_fill_color),     // 中间：较亮
            ContextCompat.getColor(context, R.color.light_fill_color),
            Color.TRANSPARENT // 终点：透明
        ),
        positions = floatArrayOf(0f, 0.3f, 0.4f, 1f) // 颜色分布的比例
    )
    // 边框线的渐变（从光源方向到终点逐渐透明）
    mBorderLinePaint.shader = createGradient(
        colorArray = intArrayOf(
            ContextCompat.getColor(context, R.color.light_border_line_color),
            Color.TRANSPARENT
        ),
        positions = floatArrayOf(0.4f, 1f)
    )
}

/** 创建线性渐变 */
private fun createGradient(colorArray: IntArray, positions: FloatArray): LinearGradient? {
    if (mCurrentPoints.size < 3) return null
    // 渐变方向：从第一个光源点到第一个终点（垂直方向）
    val startPoint = mCurrentPoints[0]
    val endPoint = mCurrentPoints[2]
    return LinearGradient(
        startPoint.x, startPoint.y, // 渐变起点（光源处）
        startPoint.x, endPoint.y,   // 渐变终点（光照最远处）
        colorArray, 
        positions, 
        Shader.TileMode.CLAMP // 超出范围时沿用边缘颜色
    )
}
```

- 填充区域使用 3 种颜色过渡（亮→较亮→透明），positions数组控制颜色变化的比例（0f 是起点，1f 是终点）。
- 边框线的渐变更简单，从中间位置开始到终点逐渐透明，避免边框在远处过于突兀。

## 四、动画实现：平滑切换光照距离

```
/** 带动画的更新光照距离 */
fun updatePointsWithAnimation(index: Int) {
    val newPoints = buildList { // 组合新的顶点集合（固定光源点+新的终点）
        addAll(initPoints)
        addAll(mAllPointsArray.get(index))
    }
    if (newPoints == mCurrentPoints) return // 若已处于目标状态，不执行动画
    cancelAnimation() // 取消当前动画（避免冲突）
    startAnimation(newPoints)
}

/** 开始动画 */
private fun startAnimation(newPoints: List<PointF>) {
    // 创建多个ValueAnimator，分别控制每个可变点的坐标变化
    val animators = createAnimator(newPoints)
    mCurrentAnimator = AnimatorSet().apply {
        playTogether(animators) // 同时执行所有点的动画
        duration = 500L // 动画时长（500ms，保证流畅度）
        interpolator = AccelerateDecelerateInterpolator() // 先加速后减速，视觉更自然
        addListener(object : AnimatorListenerAdapter() {
            override fun onAnimationEnd(animation: Animator) {
                // 动画结束后更新最终坐标
                mCurrentPoints = newPoints.toMutableList()
                updateView()
            }
        })
        start()
    }
    // 手动控制刷新频率，避免过度绘制
    startManualInvalidate()
}

/** 创建每个点的动画 */
private fun createAnimator(newPoints: List<PointF>): List<ValueAnimator> {
    return mCurrentPoints.mapIndexedNotNull { index, startPoint ->
        // 前2个点是固定光源点，不参与动画；只动画后面的终点
        if (index < 2 || index >= newPoints.size) return@mapIndexedNotNull null
        val endPoint = newPoints[index]
        // 用PointEvaluator插值计算点的中间位置
        ValueAnimator.ofObject(
            PointEvaluator(),
            startPoint,
            endPoint
        ).apply {
            addUpdateListener {
                // 实时更新当前点的坐标
                mCurrentPoints[index] = it.animatedValue as PointF
            }
        }
    }
}

/** 点坐标的插值器（计算动画过程中的中间位置） */
inner class PointEvaluator : TypeEvaluator<PointF> {
    override fun evaluate(fraction: Float, startValue: PointF, endValue: PointF): PointF {
        // 线性插值：start + (end - start) * 进度
        return PointF(
            startValue.x + (endValue.x - startValue.x) * fraction,
            startValue.y + (endValue.y - startValue.y) * fraction
        )
    }
}
```

- 仅对可变的终点执行动画（光源点固定），减少动画计算量。
- 使用PointEvaluator实现点坐标的线性插值，确保过渡平滑。
- 采用AccelerateDecelerateInterpolator，动画节奏更符合物理直觉（开始慢→中间快→结束慢）。

### 4.2 性能优化：控制刷新频率

动画过程中若频繁调用invalidate()会导致过度绘制，通过手动控制刷新频率优化性能：  
动画时长 500ms，按 60 帧 / 秒计算，每帧间隔约 8ms，通过postDelayed控制刷新频率，避免系统自动刷新导致的冗余绘制。

```
/** 控制刷新频率，避免每帧都刷新 */
private fun startManualInvalidate() {
    removeCallbacks(invalidateRunnable)
    post(invalidateRunnable)
}

private val invalidateRunnable = object : Runnable {
    // 计算每帧的延迟（60帧/秒，每帧约16ms）
    val frameDelay = ANIMATION_DURATION / FRAME_RATE // 500ms / 60 ≈ 8ms
    override fun run() {
        if (mCurrentAnimator?.isRunning == true) {
            postInvalidate() // 刷新View
            postDelayed(this, frameDelay) // 延迟下一帧刷新
        }
    }
}
```

## 五、集成使用

在 Activity/Fragment 中，只需通过简单调用即可控制灯光距离的切换：

```
 <com.nio.settings.animation.custom.CarHeadLightView
        android:id="@+id/chl_car_light"
        android:layout_width="match_parent"
        android:layout_height="@dimen/fy_size_464px"
        android:visibility="gone" />
 <com.nio.firefly.imageview.FireflyImageView
        android:layout_width="@dimen/fy_size_600px"
        android:layout_height="@dimen/fy_size_464px"
        android:layout_gravity="end"
        android:layout_marginEnd="@dimen/fy_size_108px"
        android:src="@drawable/bg_light_car_model" />
```

```
 // 显示灯光调节动画
 fun playDistanceEnableAnimation() {
     binding.chlCarLight.createAlphaAnimator(
         fromAlpha = 0f,
         toAlpha = 1f,
         onEnd = { binding.chlCarLight.isVisible = true }
     ).start()
 }

 // 隐藏灯光调节动画
 fun playDistanceDisableAnimation() {
     binding.chlCarLight.createAlphaAnimator(
         fromAlpha = 1f,
         toAlpha = 0f,
         onEnd = { binding.chlCarLight.isVisible = false }
     ).start()
 }

 private fun View.createAlphaAnimator(
        start: Float,
        end: Float,
        config: AnimationConfig = AnimationConfig(),
        state: CarLightState,
        onStart: (() -> Unit)? = null, // 新增启动回调
        onEnd: (() -> Unit)? = null
    ): ObjectAnimator {
        LogUtil.i(TAG, "createAlphaAnimator: $start, $end, ${config.duration}), ${config.delay}, state: $state")
        return ObjectAnimator.ofFloat(this, View.ALPHA, start, end).apply {
            duration = config.duration
            interpolator = config.interpolator
            startDelay = config.delay
            addListener(
                onStart = {
                    onStart?.invoke()
                },
                onEnd = {
                    onEnd?.invoke()
                })
        }
    }

 // 切换到距离等级2（0-4）
 binding.btnLevel2.setOnClickListener {
     binding.chlCarLight.updatePointsWithAnimation(2)
 }
```

## 六、自定义CarHeadLightView完整代码

```
class CarHeadLightView @JvmOverloads constructor(
    context: Context, attrs: AttributeSet? = null, defStyleAttr: Int = 0
) : View(context, attrs, defStyleAttr) {

    // 光照画笔
    private val mLightPaint by lazyPaint {
        style = Paint.Style.FILL
        isAntiAlias = true // 抗锯齿
    }
    // 边框画笔
    private val mBorderLinePaint by lazyPaint {
        style = Paint.Style.STROKE
        strokeWidth = 2f
        isAntiAlias = true // 抗锯齿
    }
    private val mPath by lazy { Path() }

    private val mLightConfig by lazy { createLightConfig() }
    // 光源位置
    private val initPoints = listOf(PointF(1228.2f, 226.4f), PointF(1395.4f, 283.4f))
    private val mArcCenterPoint = PointF(1292.9f, 264.9f)
    private var mCurrentPoints = mutableListOf<PointF>()
    private var mCurrentAnimator: Animator? = null
    private var mArcPathParams: Pair<FloatArray, RectF>? = null

    // 初始化2个点的坐标
    private val mAllPointsArray: SparseArray<List<PointF>> = SparseArray<List<PointF>>().apply {
        put(0, listOf(
            PointF(1329.6f, 464f),  // 点1
            PointF(837.2f, 464f),  // 点2
        ))
        put(1, listOf(
            PointF(1314.6f, 464f),  // 点1
            PointF(765.3f, 464f),  // 点2
        ))
        put(2, listOf(
            PointF(1301.4f, 464f),  // 点1
            PointF(678.3f, 464f),  // 点2
        ))
        put(3, listOf(
            PointF(1279.2f, 464f),  // 点1
            PointF(518.4f, 464f),  // 点2
        ))
        put(4, listOf(
            PointF(1258.8f, 464f),  // 点1
            PointF(333.9f, 464f),  // 点2
        ))
    }

    init {
        setLayerType(LAYER_TYPE_HARDWARE, null)
        //初始起点固定，只需计算一次。如有变动，可变更后计算在做缓存
        mArcPathParams = buildArcPath()
    }

    /**
     * 更新光照坐标并触发重绘
     */
    fun updatePoints(index: Int) {
        mCurrentPoints = buildList {
            addAll(initPoints)
            addAll(mAllPointsArray.get(index))
        }.toMutableList()
        LogUtil.i(TAG, "updatePoints index: $index")
        updateView()
    }

    /**
     * 带动画的更新光照坐标.
     */
    fun updatePointsWithAnimation(index: Int) {
        LogUtil.i(TAG, "updatePointsWithAnimation index: $index")
        val newPoints = buildList {
            addAll(initPoints)
            addAll(mAllPointsArray.get(index))
        }
        if (newPoints == mCurrentPoints) {
            return
        }
        cancelAnimation()
        startAnimation(newPoints)
    }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        if (mCurrentPoints.size < 4) {
            LogUtil.w(TAG, "Insufficient points for drawing")
            return
        }
        drawLightArea(canvas)
        drawBorderLine(canvas)
    }

    /**
     * 绘制光照区域.
     */
    private fun drawLightArea(canvas: Canvas) {
        mPath.apply {
            reset()
            moveTo(mCurrentPoints[0].x, mCurrentPoints[0].y)
            val (startAngle, sweepAngle) = mArcPathParams?.first ?: return
            val rect = mArcPathParams?.second ?: return
            arcTo(rect, startAngle, sweepAngle)
            lineTo(mCurrentPoints[2].x, mCurrentPoints[2].y)
            lineTo(mCurrentPoints[3].x, mCurrentPoints[3].y)
            canvas.drawPath(this, mLightPaint)
        }
    }

    /**
     * 绘制边框线.
     */
    private fun drawBorderLine(canvas: Canvas) {
        val lines = floatArrayOf(
            mCurrentPoints[0].x, mCurrentPoints[0].y, mCurrentPoints[3].x, mCurrentPoints[3].y,
            mCurrentPoints[1].x, mCurrentPoints[1].y, mCurrentPoints[2].x, mCurrentPoints[2].y)
        canvas.drawLines(lines, mBorderLinePaint)
    }

    /**
     * 计算弧形边.
     */
    private fun buildArcPath(): Pair<FloatArray, RectF>? {
        if (initPoints.isEmpty()) return null
        val (centerX, centerY, radius) = calculateArcParams() ?: return null
        val startAngle = calculateStartAngle(centerX, centerY)
        val sweepAngle = calculateSweepAngle(centerX, centerY)
        val rect = RectF(
            centerX - radius,
            centerY - radius,
            centerX + radius,
            centerY + radius
        )
        return Pair(floatArrayOf(startAngle, sweepAngle), rect)
    }

    /**
     * 计算圆弧参数.
     */
    private fun calculateArcParams(): FloatArray? {
        if (initPoints.isEmpty()) return null
        val p1 = initPoints[0]
        val p2 = initPoints[1]
        return calculateCenterAndRadius(
            p1.x, p1.y,
            mArcCenterPoint.x, mArcCenterPoint.y,
            p2.x, p2.y
        )
    }

    /**
     * 计算开始角度.
     */
    private fun calculateStartAngle(centerX: Float, centerY: Float): Float {
        val p = initPoints[0]
        return Math.toDegrees(atan2(p.y - centerY, p.x - centerX).toDouble()).toFloat()
    }

    /**
     * 计算扫过的角度.
     */
    private fun calculateSweepAngle(centerX: Float, centerY: Float): Float {
        val p1 = initPoints[0]
        val p2 = initPoints[1]
        val angle1 = Math.toDegrees(atan2(p1.y - centerY, p1.x - centerX).toDouble()).toFloat()
        val angle2 = Math.toDegrees(atan2(p2.y - centerY, p2.x - centerX).toDouble()).toFloat()
        return angle2 - angle1
    }

    /**
     * 计算圆心和半径.
     */
    private fun calculateCenterAndRadius(
        x1: Float, y1: Float, x2: Float,
        y2: Float, x3: Float, y3: Float
    ): FloatArray {
        val xc: Float
        val yc: Float
        val ma = (y2 - y1) / (x2 - x1)
        val mb = (y3 - y2) / (x3 - x2)
        xc = (ma * mb * (y1 - y3) + mb * (x1 + x2) - ma * (x2 + x3)) / (2 * (mb - ma))
        yc = -1 * (xc - (x1 + x2) / 2) / ma + (y1 + y2) / 2
        val radius = sqrt(((x1 - xc) * (x1 - xc) + (y1 - yc) * (y1 - yc)).toDouble())
            .toFloat()
        return floatArrayOf(xc, yc, radius)
    }

    private fun startAnimation(newPoints: List<PointF>) {
        val animators = createAnimator(newPoints)
        mCurrentAnimator = AnimatorSet().apply {
            playTogether(animators)
            duration = ANIMATION_DURATION
            interpolator = AccelerateDecelerateInterpolator()
            addListener(object : AnimatorListenerAdapter() {
                override fun onAnimationEnd(animation: Animator) {
                    finishAnimation(newPoints)
                }

                override fun onAnimationCancel(animation: Animator) {
                    finishAnimation(newPoints)
                }
            })
            start()
        }
        startManualInvalidate()
    }

    private fun createAnimator(newPoints: List<PointF>): List<ValueAnimator> {
        return mCurrentPoints.mapIndexedNotNull { index, startPoint ->
            // 初始点和结束点相同则不进行动画
            if (index < 2 || index >= newPoints.size) return@mapIndexedNotNull null
            val endPoint = newPoints[index]
            ValueAnimator.ofObject(
                PointEvaluator(),
                startPoint,
                endPoint
            ).apply {
                addUpdateListener {
                    // 动态更新点坐标
                    mCurrentPoints[index] = it.animatedValue as PointF
                }
            }
        }
    }

    /**
     * 由于线性透明度渐变的起点和终点不变，所以只需在动画完成后再次刷新校准ui即可.
     */
    private fun finishAnimation(finalPoints: List<PointF>) {
        mCurrentPoints = finalPoints.toMutableList()
        updateView()
    }

    /**
     * 控制invalidate的频率，避免过度刷新.
     */
    private fun startManualInvalidate() {
        removeCallbacks(invalidateRunnable)
        post(invalidateRunnable)
    }

    private val invalidateRunnable = object : Runnable {
        val frameDelay = ANIMATION_DURATION / FRAME_RATE
        override fun run() {
            if (mCurrentAnimator?.isRunning == true) {
                postInvalidate()
                postDelayed(this, frameDelay)
            }
        }
    }

    /**
     * 更新ui.
     */
    private fun updateView() {
        updateGradients()
        postInvalidate()
    }

    /**
     * 更新渐变（从光源中心向远端扩散）.
     */
    private fun updateGradients() {
        mLightPaint.shader = createGradient(mLightConfig.fillColors, mLightConfig.fillPositions)
        mBorderLinePaint.shader = createGradient(mLightConfig.borderColors, mLightConfig.borderPositions)
        LogUtil.e(TAG, "updateGradient")
    }

    override fun onDetachedFromWindow() {
        super.onDetachedFromWindow()
        cancelAnimation()
    }

    /**
     * 取消动画.
     */
    private fun cancelAnimation() {
        mCurrentAnimator?.let {
            if (it.isRunning) it.cancel()
            it.removeAllListeners()
        }
        mCurrentAnimator = null
    }

    /**
     * 创建线性渐变，从起点开始透明度渐变.
     */
    private fun createGradient(colorArray: IntArray, positions: FloatArray): LinearGradient? {
        if (mCurrentPoints.size < 3) return null
        val startPoint = mCurrentPoints.getOrNull(0) ?: PointF()
        val endPoint = mCurrentPoints.getOrNull(2) ?: PointF()
        return LinearGradient(
            startPoint.x, startPoint.y, startPoint.x, endPoint.y,
            colorArray, positions,
            Shader.TileMode.CLAMP
        )
    }

    /**
     * 光束参数配置.
     */
    private fun createLightConfig(): LightConfig {
        return LightConfig(
            fillColors = intArrayOf(ContextCompat.getColor(context, R.color.light_fill_init_color),
                ContextCompat.getColor(context, R.color.light_fill_color),
                ContextCompat.getColor(context, R.color.light_fill_color),
                Color.TRANSPARENT),
            fillPositions = floatArrayOf(0f, 0.3f, 0.4f, 1f),
            borderColors = intArrayOf(ContextCompat.getColor(context, R.color.light_border_line_color), Color.TRANSPARENT),
            borderPositions = floatArrayOf(0.4f, 1f)
        )
    }

    private inline fun lazyPaint(crossinline block: Paint.() -> Unit): Lazy<Paint> =
        lazy { Paint().apply(block) }

    data class LightConfig(
        val fillColors: IntArray,
        val fillPositions: FloatArray,
        val borderColors: IntArray,
        val borderPositions: FloatArray
    ) {
        override fun equals(other: Any?): Boolean {
            return super.equals(other)
        }

        override fun hashCode(): Int {
            return super.hashCode()
        }
    }

    inner class PointEvaluator : TypeEvaluator<PointF> {
        override fun evaluate(fraction: Float, startValue: PointF, endValue: PointF): PointF {
            return PointF(
                startValue.x + (endValue.x - startValue.x) * fraction,
                startValue.y + (endValue.y - startValue.y) * fraction
            )
        }
    }

    companion object {
        private const val TAG = "HeadLightView"
        private const val ANIMATION_DURATION = 500L
        private const val FRAME_RATE = 60
    }
}
```

## 七、总结与扩展

本文实现的 CarHeadLightView 通过自定义 View 的绘制和动画能力，成功模拟了汽车灯光距离调节的效果，通过这种实现方式，不仅能满足汽车灯光调节的需求，还可推广到其他需要 “动态区域绘制” 的场景（如雷达扫描、音量可视化等），具有较强的通用性。
