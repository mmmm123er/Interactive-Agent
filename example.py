from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks

semantic_cls = pipeline(Tasks.nli, 'iic/nlp_structbert_nli_chinese-tiny', model_revision='master')

# ============================================================
# NLI 推理结果格式
# 模型输出: {"labels": ["蕴涵", "中立", "矛盾"], "scores": [...]}
# 标签索引: 蕴涵=0, 中立=1, 矛盾=2
# 映射为: {"矛盾": 0, "蕴涵": 1, "中立": 2}
# 得分 = 矛盾 - 蕴涵  (得分范围: [-1, 1])
# ============================================================
HYPOTHESIS = "这是闲聊"


def load_lines(filepath: str) -> list[str]:
    lines = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and not stripped.startswith("-"):
                lines.append(stripped)
    return lines


# ============================================================
# 判断标准总结
# ============================================================
def print_judgment_criteria():
    print("""
╔══════════════════════════════════════════════════════════════════════════╗
║                    闲聊 vs 指令任务 — NLI 判断标准总结                    ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║  模型输入: (用户文本, "这是闲聊")                                        ║
║  计算公式: score = 矛盾(contradiction) - 蕴涵(entailment)                ║
║                                                                          ║
║  ┌────────────┬──────────────────────────────────────────────────────┐  ║
║  │  类别      │  判断标准                                             │  ║
║  ├────────────┼──────────────────────────────────────────────────────┤  ║
║  │  闲聊      │  文本与"这是闲聊"一致/蕴涵 → 矛盾低, 蕴涵高          │  ║
║  │  (chat)    │  score 低(甚至为负) → 被判定为闲聊                    │  ║
║  │            │  特征: 打招呼/自我介绍/情感表达/日常寒暄/感谢/道别等  │  ║
║  ├────────────┼──────────────────────────────────────────────────────┤  ║
║  │  指令任务  │  文本与"这是闲聊"矛盾 → 矛盾高, 蕴涵低                │  ║
║  │  (task)    │  score 高(正值大) → 被判定为任务指令                   │  ║
║  │            │  特征: 动作命令/查询/设置/导航/控制/告警等明确意图     │  ║
║  ├────────────┼──────────────────────────────────────────────────────┤  ║
║  │  边界案例  │  命令式闲聊(如"你过来一下") vs 任务指令               │  ║
║  │  (border)  │  二者在句式上相似, 是NLI区分最难的部分                │  ║
║  │            │  依赖语义上下文: 纯社交互动 vs 功能执行意图            │  ║
║  └────────────┴──────────────────────────────────────────────────────┘  ║
║                                                                          ║
║  关键理解:                                                              ║
║  • 蕴涵(entailment)强 → 文本很像"这是在闲聊" → 分类为闲聊              ║
║  • 矛盾(contradiction)强 → 文本完全不是"闲聊" → 分类为指令任务         ║
║  • 中立(neutral)主导 → 文本与闲聊的语义关系不明确 → 边界模糊区         ║
║  • score = contradiction - entailment 放大了区分度                      ║
║  • 阈值 threshold 控制保守/激进的权衡:                                 ║
║    低阈值 → 宁可误报(FP↑)不可漏报(FN↓), 适合安全场景                  ║
║    高阈值 → 宁可漏报(FN↑)不可误报(FP↓), 适合高精确定场景               ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
""")


# ============================================================
# 演示示例: 展示具体文本的 NLI 推理结果
# ============================================================
def run_demo_examples():
    print("=" * 80)
    print("                      演示示例: NLI推理结果展示")
    print("=" * 80)

    demo_texts = {
        "闲聊-问候": "你好啊",
        "闲聊-日常": "今天天气真好",
        "闲聊-情感": "你开心吗",
        "闲聊-感谢": "谢谢",
        "闲聊-道别": "再见",
        "闲聊-简短": "嗯",
        "闲聊-命令式": "你过来一下",
        "闲聊-命令式": "你别走",
        "指令-导航": "往前走三米",
        "指令-查询": "检查一下系统状态",
        "指令-设置": "设置音量为百分之五十",
        "指令-控制": "暂停任务",
        "指令-告警": "启动安全模式",
        "指令-充电": "去充电",
    }

    print(f"\n{'类别':<12} {'用户输入':<20} {'蕴涵':>8} {'中立':>8} {'矛盾':>8} {'score':>8} {'预测':>6}")
    print("-" * 80)

    for category, text in demo_texts.items():
        result = semantic_cls(input=(text, HYPOTHESIS))
        d = dict(zip(result["labels"], result["scores"]))
        ent = d.get("蕴涵", 0)
        neu = d.get("中立", 0)
        con = d.get("矛盾", 0)
        score = con - ent
        pred = "指令" if score >= 0.12 else "闲聊"
        print(f"{category:<12} {text:<20} {ent:>8.4f} {neu:>8.4f} {con:>8.4f} {score:>8.4f} {pred:>6}")

    print()
    print("-" * 80)
    print("  解读: 闲聊文本蕴涵高、矛盾低、score偏负; 指令文本矛盾高、蕴涵低、score偏正")

    # 详细展示一条边界案例
    print(f"\n  ★ 边界案例深度分析:")
    border_texts = {
        "命令式闲聊": [
            "你过来一下",
            "你别走",
            "你坐下吧",
            "你别说话",
        ],
        "短指令": [
            "过来",
            "坐下",
            "停",
        ],
    }
    for cat, texts in border_texts.items():
        print(f"\n  【{cat}】")
        for text in texts:
            result = semantic_cls(input=(text, HYPOTHESIS))
            d = dict(zip(result["labels"], result["scores"]))
            ent = d.get("蕴涵", 0)
            neu = d.get("中立", 0)
            con = d.get("矛盾", 0)
            score = con - ent
            pred = "指令" if score >= 0.12 else "闲聊"
            print(f"    {text:<12}  蕴涵={ent:.4f}  中立={neu:.4f}  矛盾={con:.4f}  score={score:.4f} → {pred}")


# ============================================================
# 加载数据
# ============================================================
task_lines = load_lines("task_commands.txt")
chat_lines = load_lines("chitchat.txt")
print(f"\n任务指令: {len(task_lines)} 条 | 闲聊用语: {len(chat_lines)} 条 | 合计: {len(task_lines)+len(chat_lines)} 条")

# ============================================================
# 打印判断标准
# ============================================================
print_judgment_criteria()

# ============================================================
# 演示示例
# ============================================================
run_demo_examples()

# ============================================================
# 批量推理，计算所有样本的得分
# ============================================================
print()
print("正在进行 NLI 批量推理...")
records: list[dict] = []

for text in task_lines:
    result = semantic_cls(input=(text, HYPOTHESIS))
    d = dict(zip(result["labels"], result["scores"]))
    ent = d.get("蕴涵", 0)
    con = d.get("矛盾", 0)
    records.append({"text": text, "true": "task", "ent": ent, "con": con, "score": con - ent})

for text in chat_lines:
    result = semantic_cls(input=(text, HYPOTHESIS))
    d = dict(zip(result["labels"], result["scores"]))
    ent = d.get("蕴涵", 0)
    con = d.get("矛盾", 0)
    records.append({"text": text, "true": "chat", "ent": ent, "con": con, "score": con - ent})

# ============================================================
# 阈值扫描：展示精确率-召回率权衡
# ============================================================
print()
print("=" * 100)
print("                      阈值扫描: 不同阈值下的指标结果")
print("=" * 100)
print(f"{'阈值':>8}  {'准确率':>8}  {'精确率':>8}  {'召回率':>8}  {'F1':>8}  {'任务正确':>8}  {'任务漏报':>6}  {'闲聊误报':>8}  {'闲聊正确':>6}  {'TPR':>8}  {'FPR':>8}")
print("-" * 100)

thresholds = [0.00, 0.05, 0.08, 0.10, 0.11, 0.12, 0.13, 0.14, 0.15, 0.16, 0.18, 0.20, 0.25, 0.30]
for th in thresholds:
    tp = sum(1 for r in records if r["true"] == "task" and r["score"] >= th)
    fn = sum(1 for r in records if r["true"] == "task" and r["score"] < th)
    fp = sum(1 for r in records if r["true"] == "chat" and r["score"] >= th)
    tn = sum(1 for r in records if r["true"] == "chat" and r["score"] < th)
    acc = (tp + tn) / len(records)
    p = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    r = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0.0
    tpr = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    print(f"{th:>8.2f}  {acc:>8.4f}  {p:>8.4f}  {r:>8.4f}  {f1:>8.4f}  {tp:>8}  {fn:>6}  {fp:>8}  {tn:>6}  {tpr:>8.4f}  {fpr:>8.4f}")


# ============================================================
# 自动计算各阈值下的完整指标 (更精细的步长)
# ============================================================
print()
print("=" * 100)
print("                      精细阈值扫描 (step=0.01, 0.0~0.5)")
print("=" * 100)
print(f"{'阈值':>8}  {'准确率':>8}  {'精确率':>8}  {'召回率':>8}  {'F1':>8}  {'任务正确':>8}  {'任务漏报':>6}  {'闲聊误报':>8}  {'闲聊正确':>6}")
print("-" * 100)

fine_thresholds = [round(x * 0.01, 2) for x in range(0, 51)]
for th in fine_thresholds:
    tp = sum(1 for r in records if r["true"] == "task" and r["score"] >= th)
    fn = sum(1 for r in records if r["true"] == "task" and r["score"] < th)
    fp = sum(1 for r in records if r["true"] == "chat" and r["score"] >= th)
    tn = sum(1 for r in records if r["true"] == "chat" and r["score"] < th)
    acc = (tp + tn) / len(records)
    p = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    r = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0.0
    print(f"{th:>8.2f}  {acc:>8.4f}  {p:>8.4f}  {r:>8.4f}  {f1:>8.4f}  {tp:>8}  {fn:>6}  {fp:>8}  {tn:>6}")


# ============================================================
# 最佳F1阈值
# ============================================================
all_scores = sorted(set(round(r["score"], 6) for r in records))
best_f1, best_th, best_m = 0, 0, {}
for th in all_scores:
    tp = sum(1 for r in records if r["true"] == "task" and r["score"] >= th)
    fn = sum(1 for r in records if r["true"] == "task" and r["score"] < th)
    fp = sum(1 for r in records if r["true"] == "chat" and r["score"] >= th)
    tn = sum(1 for r in records if r["true"] == "chat" and r["score"] < th)
    _acc = (tp + tn) / len(records)
    p = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    r = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0.0
    if f1 > best_f1:
        best_f1, best_th = f1, th
        best_m = {"tp": tp, "fn": fn, "fp": fp, "tn": tn, "acc": _acc, "p": p, "r": r}

print()
print("=" * 70)
print(f"  最优阈值 (最大F1) = {best_th:.4f}")
print("=" * 70)
print(f"  假设句      : {HYPOTHESIS}")
print(f"  判断公式    : score = contradiction - entailment")
print(f"  分类规则    : score >= {best_th:.4f} → 任务指令, 否则 → 闲聊")
print(f"  样本总数    : {len(records)}")
print(f"  正确分类    : {best_m['tp'] + best_m['tn']}")
print(f"  错误分类    : {best_m['fp'] + best_m['fn']}")
print()
print(f"  准确率      : {best_m['acc']:.4f}  ({best_m['acc']*100:.2f}%)")
print(f"  精确率      : {best_m['p']:.4f}  ({best_m['p']*100:.2f}%)")
print(f"  召回率      : {best_m['r']:.4f}  ({best_m['r']*100:.2f}%)")
print(f"  F1分数      : {best_f1:.4f}")
print()
print(f"  混淆矩阵    :")
print(f"               预测=task    预测=chat")
print(f"    实际=task    {best_m['tp']:>6}        {best_m['fn']:>6}")
print(f"    实际=chat    {best_m['fp']:>6}        {best_m['tn']:>6}")
print()
print(f"  任务召回率  : {best_m['tp']}/{len(task_lines)} = {best_m['tp']/len(task_lines)*100:.1f}%")
print(f"  闲聊召回率  : {best_m['tn']}/{len(chat_lines)} = {best_m['tn']/len(chat_lines)*100:.1f}%")
print(f"  误报率      : {best_m['fp']}/{len(chat_lines)} = {best_m['fp']/len(chat_lines)*100:.1f}%")
print(f"  漏报率      : {best_m['fn']}/{len(task_lines)} = {best_m['fn']/len(task_lines)*100:.1f}%")


# ============================================================
# 误判样本展示（最优阈值下）
# ============================================================
TH = best_th
fp_samples = sorted(
    [r for r in records if r["true"] == "chat" and r["score"] >= TH],
    key=lambda r: -r["score"]
)
fn_samples = sorted(
    [r for r in records if r["true"] == "task" and r["score"] < TH],
    key=lambda r: r["score"]
)

if fn_samples:
    print()
    print(f"  任务误判为闲聊 (False Negative, 共 {len(fn_samples)} 条):")
    for r in fn_samples[:10]:
        print(f"    [{r['score']:.4f}] {r['text']}")

if fp_samples:
    print()
    print(f"  闲聊误判为任务 (False Positive, 共 {len(fp_samples)} 条, 仅展示得分最高的前15):")
    for r in fp_samples[:15]:
        print(f"    [蕴={r['ent']:.4f} 矛={r['con']:.4f} s={r['score']:.4f}] {r['text']}")


# ============================================================
# 各阈值下的场景推荐
# ============================================================
print()
print("=" * 70)
print("  阈值选择建议 — 不同阈值下的指标结果对比")
print("=" * 70)

scenarios = [
    (0.08, "宁可误报不可漏报（安全优先, 召回率最高）"),
    (0.10, "偏向召回率（容忍部分误报）"),
    (0.12, "均衡模式（F1最优附近）"),
    (0.14, "降低误报, 提高精确率"),
    (0.16, "宁可漏报不可误报（高精确率）"),
]

print(f"\n  {'阈值':<8} {'准确率':<10} {'精确率':<10} {'召回率':<10} {'F1':<10} {'适用场景':<40}")
print("  " + "-" * 88)

for th, desc in scenarios:
    tp = sum(1 for r in records if r["true"] == "task" and r["score"] >= th)
    fn = sum(1 for r in records if r["true"] == "task" and r["score"] < th)
    fp = sum(1 for r in records if r["true"] == "chat" and r["score"] >= th)
    tn = sum(1 for r in records if r["true"] == "chat" and r["score"] < th)
    acc = (tp + tn) / len(records)
    p = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    r = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0.0
    print(f"  {th:<8.2f} {acc:<10.4f} {p:<10.4f} {r:<10.4f} {f1:<10.4f} {desc:<40}")

print(f"""
  使用方法: 在 classify_intent() 函数内修改 THRESHOLD 变量即可。
"""
)