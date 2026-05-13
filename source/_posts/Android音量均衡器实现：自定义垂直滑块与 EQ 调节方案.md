---
title: Android音量均衡器实现：自定义垂直滑块与 EQ 调节方案
date: 2025-07-14 15:15:28
categories:
  - android
tags:
  - android
  - java
---
在音频处理应用中，均衡器是一个核心功能，它允许用户调整不同频段的增益来优化音频输出。本文将详细介绍如何在Android中实现一个美观且功能完整的垂直均衡器控件。

## 一、需求分析与设计思路

### 1.1 核心需求

- 垂直方向的滑动条（区别于Android原生水平SeekBar）
- 支持正负增益调节（±6dB范围）
- 中央显示当前增益值
- 可自定义视觉样式（宽度、颜色、圆角等）
- 多个频段独立控制

### 1.2 设计思路

- 自定义View实现垂直滑动条
- 使用Canvas绘制背景、进度条和文本
- 触摸事件处理实现交互逻辑
- 多个频段组合形成完整均衡器

## 二、核心实现：VerticalSeekBar

### 2.1 自定义属性定义

```
    <declare-styleable name="VerticalSeekBar">
        <attr name="seekBarWidth" format="dimension" />
        <attr name="seekBarBackGroundRadius" format="dimension" />
        <attr name="seekBarStartRadius" format="dimension" />
        <attr name="seekBarEndRadius" format="dimension" />
        <attr name="seekBarBackGroundColor" format="color" />
        <attr name="seekBarProgressColor" format="color" />
        <attr name="indicatorTextColor" format="color" />
        <attr name="indicatorTextSize" format="dimension" />
    </declare-styleable>
```

### 2.2 关键实现代码分析

1. 初始化与绘制准备

```
private void initPaint() {
   // 进度条背景画笔
   paintBackGround = new Paint();
   paintBackGround.setColor(seekBarBackGroundColor);
   paintBackGround.setStyle(Paint.Style.FILL);
   
   // 进度条画笔
   paintSeekBarProgress = new Paint();
   paintSeekBarProgress.setColor(seekBarProgressColor);
   paintSeekBarProgress.setStyle(Paint.Style.FILL);
   
   // 文本画笔
   paintIndicatorText = new Paint();
   paintIndicatorText.setColor(indicatorTextColor);
   paintIndicatorText.setTextSize(indicatorTextSize);
   paintIndicatorText.setTextAlign(Paint.Align.CENTER);
   paintIndicatorText.setTypeface(Typeface.DEFAULT_BOLD);
}
```

2. 动态计算与绘制进度条

- updateRects根据当前进度动态计算进度条的绘制区域，实现进度与视觉位置的对应（正值向上，负值向下）
- 进度条形状动态变化：使用Path.addRoundRect的 8 参数重载，为矩形的四个角设置不同的圆角半径，实现进度条与中心的平滑衔接
- 文字垂直居中计算：通过FontMetrics获取字体的 ascent（上沿）和 descent（下沿），计算中间位置作为文字的 Y 坐标

```
private void updateRects() {
    backgroundRect.set(0, 0, width, height); // 背景区域为整个View
    // 根据进度计算进度区域（正值在上，负值在下）
    if (progress > 0) {
        // 正值进度：从中心向上延伸
        progressRect.set(0, mCenterY - (progress / (float)mMaxProgress) * mCenterY, width, mCenterY);
    } else if (progress < 0) {
        // 负值进度：从中心向下延伸
        progressRect.set(0, mCenterY, width, mCenterY + ((-progress) / (float)mMaxProgress) * mCenterY);
    } else {
        // 进度为0时，进度区域为一条线
        progressRect.set(0, mCenterY, width, mCenterY);
    }
}

@Override
protected void onDraw(Canvas canvas) {
    super.onDraw(canvas);

    // 1. 绘制背景（圆角矩形）
    canvas.drawRoundRect(backgroundRect, mBackGroundRadius, mBackGroundRadius, paintBackGround);

    // 2. 绘制进度条（根据进度绘制不同形状）
    drawProgress(canvas);

    // 3. 绘制进度文本（当前进度值）
    Paint.FontMetrics fm = paintIndicatorText.getFontMetrics();
    // 计算文字垂直居中的Y坐标（基于字体度量）
    float textY = mCenterY - (fm.descent - (-fm.ascent + fm.descent) / FLOAT_2);
    canvas.drawText(String.valueOf(progress), mCenterX, textY, paintIndicatorText);
}

private void drawProgress(Canvas canvas) {
    progressPath.reset();
    if (progress == 0) {
        // 进度为0：绘制中心圆形指示器
        float top = mCenterY - mStartRadius;
        float bottom = mCenterY + mStartRadius;
        mProgressRectZero.set(0, topBound, width, bottomBound);
        progressPath.addRoundRect(mProgressRectZero, mStartRadius, mStartRadius, Path.Direction.CW);
    } else if (progress > 0) {
        // 正值进度：上部大圆角，下部与中心衔接
        float tr = Math.min(mEndRadius, mCenterY - progressRect.top);
        tr = Math.max(tr, mStartRadius);
        float top = Math.min(progressRect.top, mCenterY - mStartRadius);
        mProgressRect1.set(0, top, width, mCenterY + mStartRadius);
        // 8个参数分别对应：左上x、左上y、右上x、右上y、右下x、右下y、左下x、左下y的圆角半径
        progressPath.addRoundRect(mProgressRect1,
                new float[]{mEndRadius, tr, mEndRadius, tr, mStartRadius, mStartRadius, mStartRadius, mStartRadius},
                Path.Direction.CW);
    } else {
        // 负值进度：下部大圆角，上部与中心衔接
        float br = Math.min(mEndRadius, progressRect.bottom - mCenterY);
        br = Math.max(br, mStartRadius);
        float bottom = Math.max(progressRect.bottom, mCenterY + mStartRadius);
        mProgressRect2.set(0, mCenterY - mStartRadius, width, bottom);
        progressPath.addRoundRect(mProgressRect2,
               new float[]{mStartRadius, mStartRadius, mStartRadius, mStartRadius, mEndRadius, br, mEndRadius, br},
                Path.Direction.CW);
    }
    canvas.drawPath(progressPath, paintSeekBarProgress);
}
```

3. 触摸事件处理

```
@Override
public boolean onTouchEvent(MotionEvent event) {
    switch (event.getAction()) {
        case MotionEvent.ACTION_DOWN:
            // 开始触摸：回调开始监听
            if (callBack != null) {
                callBack.onStartTrackingTouch(this);
            }
        case MotionEvent.ACTION_MOVE:
            // 滑动中：计算进度并更新
            float touchY = event.getY(); // 触摸点Y坐标
            int newProgress;
            if (touchY < mCenterY) {
                // 触摸点在中心上方：计算正值进度
                newProgress = fixProgress(mMaxProgress * (1 - touchY / mCenterY));
            } else {
                // 触摸点在中心下方：计算负值进度
                newProgress = -fixProgress(mMaxProgress * ((touchY - mCenterY) / mCenterY));
            }
            setProgress(newProgress); // 更新进度
            break;
        case MotionEvent.ACTION_UP:
        case MotionEvent.ACTION_CANCEL:
            // 结束触摸：回调结束监听
            if (callBack != null) {
                callBack.onStopTrackingTouch(this);
            }
            break;
    }
    return true; // 消费触摸事件
}

// 修正进度值（确保在有效范围，处理浮点数转整数）
public int fixProgress(float value) {
    return (int) (value > 1F ? Math.ceil(value) : Math.round(value));
}
```

## 三、均衡器整合：多频段调节实现

单个 VerticalSeekBar 只能调节一个频段，实际均衡器需要多个滑块分别控制不同频率，下面解析如何整合这些组件：

### 3.1 布局文件：定义多滑块布局

在 XML 布局中，为每个频段定义一个 VerticalSeekBar，并设置自定义属性：

```
<LinearLayout
    xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:app="http://schemas.android.com/apk/res-auto"
    android:orientation="horizontal"
    android:layout_width="match_parent"
    android:layout_height="wrap_content">

    <!-- 80Hz频段滑块 -->
    <com.nio.settings.widget.VerticalSeekBar
        android:id="@+id/sb_equalizer_80hz"
        style="@style/SoundFieldEQSeekBar"
        android:layout_width="@dimen/fy_size_200px"
        android:layout_height="@dimen/fy_size_720px"
        android:layout_marginStart="@dimen/fy_size_160px"
        android:layout_marginTop="@dimen/fy_size_72px"
        app:layout_constraintStart_toStartOf="parent"
        app:layout_constraintTop_toTopOf="parent" />

    <com.nio.settings.widget.VerticalSeekBar
        android:id="@+id/sb_equalizer_200hz"
        style="@style/SoundFieldEQSeekBar"
        android:layout_width="@dimen/fy_size_200px"
        android:layout_height="@dimen/fy_size_720px"
        app:layout_constraintStart_toEndOf="@id/sb_equalizer_80hz"
        app:layout_constraintTop_toTopOf="@id/sb_equalizer_80hz" />
        <!-- 相同属性略 -->/>

    <!-- 其他频段滑块（400Hz、1kHz、2.5kHz、6kHz、14kHz） -->
    <!-- ... -->

</LinearLayout>
```

### 3.2 代码初始化：绑定滑块与频段

在 Activity 或 Fragment 中初始化所有滑块，并设置监听：

```
public class EQFragment extends Fragment implements VerticalSeekBar.OnSeekBarChangeListener {
    private static final int CONT_EQ_SIZE = 7; // 7个频段
    private VerticalSeekBar[] mEqualizers = new VerticalSeekBar[CONT_EQ_SIZE];
    private AudioManager mAudioManager;

    // 滑块ID数组（与布局中定义的ID对应）
    private final int[] mEqualizersRids = {
        R.id.sb_equalizer_80hz,
        R.id.sb_equalizer_200hz,
        R.id.sb_equalizer_400hz,
        R.id.sb_equalizer_1khz,
        R.id.sb_equalizer_2_5khz,
        R.id.sb_equalizer_6khz,
        R.id.sb_equalizer_14khz
    };

    // 频段文本ID数组（显示"80Hz"等）
    private final int[] mEqualizersTvHzRids = {
        R.id.tv_equalizer_80hz,
        // ... 其他文本ID
    };

    @Override
    public View onCreateView(LayoutInflater inflater, ViewGroup container, Bundle savedInstanceState) {
        View view = inflater.inflate(R.layout.fragment_eq, container, false);
        mAudioManager = (AudioManager) getContext().getSystemService(Context.AUDIO_SERVICE);
        initEqualizers(view); // 初始化滑块
        return view;
    }

    private void initEqualizers(View view) {
        for (int i = 0; i < mEqualizersRids.length; i++) {
            // 绑定滑块并设置监听
            VerticalSeekBar seekBar = view.findViewById(mEqualizersRids[i]);
            if (seekBar != null) {
                seekBar.setOnSeekBarChangeListener(this);
                mEqualizers[i] = seekBar;
            }
            // 初始化频段文本（如"80Hz"）
            TextView tv = view.findViewById(mEqualizersTvHzRids[i]);
            if (tv != null) {
                String text = getString(R.string.fy_settings_equalizer_title_hz, getFreqText(i));
                tv.setText(Html.fromHtml(text, Html.FROM_HTML_MODE_LEGACY));
            }
        }
    }

    private String getFreqText(int index) {
        // 返回对应索引的频率文本（80Hz、200Hz等）
        String[] freqs = {"80Hz", "200Hz", "400Hz", "1kHz", "2.5kHz", "6kHz", "14kHz"};
        return freqs[index];
    }
}
```

### 3.3 监听与生效：将调节值应用到音频系统

通过OnSeekBarChangeListener监听滑块变化，并在调节结束后将所有频段的进度同步到音频系统：

```
@Override
public void onProgressChanged(VerticalSeekBar seekBar, int progress, boolean fromUser) {
    // 调节过程中实时更新UI（可选）
    if (fromUser) {
        seekBar.setProgress(progress); // 确保进度正确设置
    }
}

@Override
public void onStartTrackingTouch(VerticalSeekBar seekBar) {
    // 开始调节（可记录初始值，用于取消操作）
}

@Override
public void onStopTrackingTouch(VerticalSeekBar seekBar) {
    // 调节结束：收集所有频段的进度并设置EQ
    int[] modes = new int[CONT_EQ_SIZE];
    for (int i = 0; i < modes.length; i++) {
        modes[i] = mEqualizers[i].getProgress(); // 获取每个滑块的当前进度
    }
    // 通过AudioManager设置EQ模式
    if (mAudioManager != null) {
        mAudioManager.setEQMode(modes);
    } else {
        Log.d(TAG, "mAudioManager is null");
    }
}
```

## 四、自定义VerticalSeekBar完整代码

```
public class VerticalSeekBar extends View {
    private static final String TAG = "VerticalSeekBar";
    private static final int MAX_PROGRESS = 6;
    private static final float FLOAT_2 = 2f;
    private final RectF backgroundRect = new RectF();
    private final RectF progressRect = new RectF();
    private final Path progressPath = new Path();
    private final RectF mProgressRectZero = new RectF();
    private final RectF mProgressRect1 = new RectF();
    private final RectF mProgressRect2 = new RectF();
    private Paint paintBackGround;
    private Paint paintSeekBarProgress;
    private Paint paintIndicatorText;
    private int mSeekBarWidth;
    private int mBackGroundRadius;
    private int mStartRadius;
    private int mEndRadius;
    // 字体大小
    private int indicatorTextSize;
    // 刻度值
    private int mMaxProgress = MAX_PROGRESS;
    private int seekBarBackGroundColor;
    private int seekBarProgressColor;
    private int indicatorTextColor;

    private int width;
    private int height;
    private int progress;
    private float mCenterX;
    private float mCenterY;

    private OnSeekBarChangeListener callBack;

    public VerticalSeekBar(Context context) {
        this(context, null);
    }

    public VerticalSeekBar(Context context, @Nullable AttributeSet attrs) {
        this(context, attrs, 0);
    }

    public VerticalSeekBar(Context context, @Nullable AttributeSet attrs, int defStyleAttr) {
        super(context, attrs, defStyleAttr);
        setWillNotDraw(false);
        final TypedArray a = context.obtainStyledAttributes(attrs, R.styleable.VerticalSeekBar, defStyleAttr, 0);
        mSeekBarWidth = a.getDimensionPixelSize(R.styleable.VerticalSeekBar_seekBarWidth,
                getContext().getResources().getDimensionPixelSize(R.dimen.fy_size_32px));
        mBackGroundRadius = a.getDimensionPixelSize(R.styleable.VerticalSeekBar_seekBarBackGroundRadius,
                getContext().getResources().getDimensionPixelSize(R.dimen.fy_size_48px));
        mStartRadius = a.getDimensionPixelSize(R.styleable.VerticalSeekBar_seekBarStartRadius,
                getContext().getResources().getDimensionPixelSize(R.dimen.fy_size_48px));
        mEndRadius = a.getDimensionPixelSize(R.styleable.VerticalSeekBar_seekBarEndRadius,
                getContext().getResources().getDimensionPixelSize(R.dimen.fy_size_48px));
        indicatorTextSize = a.getDimensionPixelSize(R.styleable.VerticalSeekBar_indicatorTextSize,
                getContext().getResources().getDimensionPixelSize(R.dimen.fy_font_32px));
        seekBarBackGroundColor = a.getColor(R.styleable.VerticalSeekBar_seekBarBackGroundColor, Color.BLACK);
        seekBarProgressColor = a.getColor(R.styleable.VerticalSeekBar_seekBarProgressColor, Color.BLACK);
        indicatorTextColor = a.getColor(R.styleable.VerticalSeekBar_indicatorTextColor, Color.BLACK);
        a.recycle();
        initPaint();
    }

    private void initPaint() {
        // 进度条背景画笔
        paintBackGround = new Paint();
        paintBackGround.setColor(seekBarBackGroundColor);
        paintBackGround.setStyle(Paint.Style.FILL);
        paintBackGround.setStrokeCap(Paint.Cap.ROUND);
        paintBackGround.setStrokeWidth(mSeekBarWidth);
        paintBackGround.setAntiAlias(true);
        // 进度条画笔
        paintSeekBarProgress = new Paint();
        paintSeekBarProgress.setColor(seekBarProgressColor);
        paintSeekBarProgress.setStyle(Paint.Style.FILL);
        paintSeekBarProgress.setStrokeWidth(mSeekBarWidth);
        paintSeekBarProgress.setAntiAlias(true);
        paintSeekBarProgress.setXfermode(new PorterDuffXfermode(PorterDuff.Mode.SRC_IN));
        // float文字画笔
        paintIndicatorText = new Paint();
        paintIndicatorText.setColor(indicatorTextColor);
        paintIndicatorText.setStyle(Paint.Style.FILL);
        paintIndicatorText.setTextSize(indicatorTextSize);
        paintIndicatorText.setAntiAlias(true);
        paintIndicatorText.setTextAlign(Paint.Align.CENTER);
        paintIndicatorText.setTypeface(Typeface.DEFAULT_BOLD);
    }

    @Override
    protected void onSizeChanged(int w, int h, int oldw, int oldh) {
        super.onSizeChanged(w, h, oldw, oldh);
        width = w;
        height = h;
        mCenterX = width / FLOAT_2;
        mCenterY = height / FLOAT_2;
        updateRects();
    }

    private void updateRects() {
        backgroundRect.set(0, 0, width, height);
        if (Float.compare(progress, 0) == 0) {
            progressRect.set(0, mCenterY, width, mCenterY);
        } else if (Float.compare(progress, 0) > 0) {
            progressRect.set(0, (float) Math.ceil(mCenterY - ((float) progress / mMaxProgress) * mCenterY), width,
                    mCenterY);
        } else {
            progressRect.set(0, mCenterY, width,
                    (float) Math.ceil(mCenterY + ((float) progress / -mMaxProgress) * mCenterY));
        }
    }

    @Override
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);

        // 绘制背景
        canvas.drawRoundRect(backgroundRect, mBackGroundRadius, mBackGroundRadius, paintBackGround);

        // 绘制进度条
        drawProgress(canvas);

        // 绘制进度值
        Paint.FontMetrics fm = paintIndicatorText.getFontMetrics();
        canvas.drawText(String.valueOf(progress), mCenterX,
                mCenterY - (fm.descent - (-fm.ascent + fm.descent) / FLOAT_2), paintIndicatorText);
    }



    private void drawProgress(Canvas canvas) {
        progressPath.reset();
        if (Float.compare(progress, 0) == 0) {
            float top;
            float bottom;
            top = mCenterY - mStartRadius;
            bottom = mCenterY + mStartRadius;
            mProgressRectZero.set(0, top, width, bottom);
            progressPath.addRoundRect(mProgressRectZero, mStartRadius, mStartRadius, Path.Direction.CW);
        } else if (Float.compare(progress, 0) > 0) {
            // 正值进度：上部大圆角，下部小圆角
            float tr = Math.min(mEndRadius, mCenterY - progressRect.top);
            tr = Math.max(tr, mStartRadius);
            float top = Math.min(progressRect.top, mCenterY - mStartRadius);
            mProgressRect1.set(0, top, width, mCenterY + mStartRadius);
            progressPath.addRoundRect(mProgressRect1,
                    new float[]{mEndRadius, tr, mEndRadius, tr, mStartRadius, mStartRadius, mStartRadius, mStartRadius},
                    Path.Direction.CW);
        } else {
            // 负值进度：上部小圆角，下部大圆角
            float br = Math.min(mEndRadius, progressRect.bottom - mCenterY);
            br = Math.max(br, mStartRadius);
            float bottom = Math.max(progressRect.bottom, mCenterY + mStartRadius);
            mProgressRect2.set(0, mCenterY - mStartRadius, width, bottom);
            progressPath.addRoundRect(mProgressRect2,
                    new float[]{mStartRadius, mStartRadius, mStartRadius, mStartRadius, mEndRadius, br, mEndRadius, br},
                    Path.Direction.CW);
        }
        canvas.drawPath(progressPath, paintSeekBarProgress);
    }

    public void setProgress(int progress) {
        this.progress = Math.max(-mMaxProgress, Math.min(mMaxProgress, progress));
        updateRects();
        if (callBack != null) {
            callBack.onProgressChanged(this, progress, false);
        }
        postInvalidate();
    }

    @Override
    public boolean dispatchTouchEvent(MotionEvent event) {
        getParent().requestDisallowInterceptTouchEvent(isEnabled());
        return super.dispatchTouchEvent(event);
    }

    // 添加触摸事件处理
    @SuppressWarnings("checkstyle:FallThrough")
    @Override
    public boolean onTouchEvent(MotionEvent event) {
        switch (event.getAction()) {
            case MotionEvent.ACTION_DOWN:
                if (callBack != null) {
                    callBack.onStartTrackingTouch(this);
                }
            case MotionEvent.ACTION_MOVE:
                float touchY = event.getY();
                int newProgress;
                if (Float.compare(touchY, mCenterY) == 0) {
                    newProgress = 0;
                } else if (Float.compare(touchY, mCenterY) < 0) {
                    newProgress = fixProgress(mMaxProgress * (1 - touchY / mCenterY));
                } else {
                    newProgress = -fixProgress(mMaxProgress * ((touchY - mCenterY) / mCenterY));
                }
                setProgress(newProgress);
            case MotionEvent.ACTION_UP:
            case MotionEvent.ACTION_CANCEL:
                if (callBack != null) {
                    callBack.onStopTrackingTouch(this);
                }
                break;
            default:
                break;
        }
        return true;
    }

    public int getProgress() {
        return progress;
    }

    public int fixProgress(float value) {
        return (int) (Float.compare(value, 1F) > 0 ? Math.ceil(value) : Math.round(value));
    }

    public void setOnSeekBarChangeListener(OnSeekBarChangeListener callBack) {
        this.callBack = callBack;
    }

    public interface OnSeekBarChangeListener {
        // 滑动前
        void onStartTrackingTouch(VerticalSeekBar seekBar);

        // 滑动中
        void onProgressChanged(VerticalSeekBar seekBar, int progress, boolean fromUser);

        // 滑动后
        void onStopTrackingTouch(VerticalSeekBar seekBar);
    }
}
```

效果预览：  
![在这里插入图片描述](/images/posts/csdn-149329660-1.png)

## 五、总结

本文通过自定义 VerticalSeekBar 实现了垂直滑块控件，并基于此构建了一个 7 频段的音量均衡器。核心要点包括：

自定义 View 的标准流程：属性解析、画笔初始化、尺寸测量、绘制逻辑、触摸处理  
垂直滑块的交互设计：触摸位置与进度的映射、正负进度的视觉区分、文本居中显示  
多频段均衡器的整合：滑块数组管理、频段文本绑定、调节值的收集与生效

通过这种实现，开发者可以快速构建一个功能完整、交互友好的音量均衡器，提升应用的音频体验。自定义 View 的灵活性使得 UI 样式可以轻松适配不同的设计需求，而解耦的架构也便于后续功能扩展。
