# 简约时尚广告风

作者 2026-08-17 选定（赛琳娜·旅行眼镜）。高端时尚品牌广告质感：**白色细体 + 大留白 + 宽字距 + 衬线大标题 + 上下渐变 scrim**。

## 达成要点

- 画布 = 成品尺寸（如 1440×2560）；底图 `object-fit:cover` 铺满
- 顶部/底部渐变 scrim：`linear-gradient(rgba(0,0,0,.6)→transparent)`，保证白字在亮背景可读
- 顶部结构：品牌小字（`letter-spacing:0.85em`，300 字重）→ 衬线大标题（Georgia/Time New Roman，100px+）→ 细线（1px `rgba(255,255,255,.75)`）→ 副标（`letter-spacing:0.42em` 小字）
- 底部结构：全宽细线（`rgba(255,255,255,.35)`）→ 城市/系列行 → 季节小字（低透明度）
- 字体：英文衬线做标题，sans 细体（Segoe UI/Microsoft YaHei）做辅助；字重 300/400 为主
- 署名「作者」：右下方，`letter-spacing:0.5em`，低透明度

## 注意点

- 文案与画面主题强相关（眼镜图配 eyewear/travel 系列文案）
- 别堆元素：品牌+标题+副标+一行底部信息足矣，多即俗
- 底图提示词预留文字区（顶部 empty space for title text），人物不居中遮挡
