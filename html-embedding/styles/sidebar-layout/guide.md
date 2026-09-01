# 侧栏式布局

横屏主力：**左 520px 文字面板 + 右侧大图**。文字绝不遮主体。

## 达成要点

- 总画布 = 侧栏宽 + 底图宽（如 520 + 1536 = 2056×1024）
- 左栏 `display:flex; flex-direction:column; overflow:hidden`；固定元素 `flex-shrink:0`；长文本 `flex:1 1 auto; min-height:0; overflow:hidden`
- 右图占位：img 铺满右侧，无文字覆盖

## 注意点

- 文字溢出（poster5 教训）：内容必须能在固定高度放下，宁可缩小字号/行距
- 竖屏/带鱼屏不套侧栏式（宽度不够）——用上下条/题跋式
