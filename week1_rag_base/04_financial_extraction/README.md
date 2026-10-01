# 第 1 周任务 4：财务指标结构化提取

## 功能说明

从年报中**结构化提取**财务指标，为第 2 周的**异动对比**准备原料。

## ⭐ 核心设计原则

> **大模型只负责"报原文"，算术永远交给代码。**

| 职责 | 承担者 | 理由 |
| :--- | :--- | :--- |
| 读原文、找数字、报单位 | **LLM** | 语言理解是 LLM 的强项 |
| 单位换算（千元→亿元） | **Python 代码** | 算术必须确定性，LLM 会算错 |
| 结构校验 | **pydantic** | 强制字段类型、防止幻觉 |

**为什么这么设计？** 财报数字动辄上亿，LLM 算错一个数量级就是 10 倍误差。让 LLM 只摘抄原文（`raw_value` + `raw_unit`），换算交给 `convert_to_100_million_yuan()` 函数，是金融 AI 的必备工程规范。

## 核心流程
用户提问："提取工业富联2025年的营业收入和净利润"
↓ db.similarity_search(query, k=8)
8 条最相关文本块
↓ 拼提示词（4 条提取规则 + JSON 格式示例）
Prompt
↓ llm.invoke()
原始 JSON 字符串
↓ 去除 ``` 包裹（如有）
↓ IndicatorResults.model_validate_json(raw)
pydantic 校验通过 ✅
↓ convert_to_100_million_yuan()
统一换算为「亿元」


## 核心知识点

| 知识点 | 说明 |
| :--- | :--- |
| **pydantic BaseModel** | 定义数据结构，自动校验类型 |
| **Field(description=...)** | 给字段加描述，帮助 LLM 理解 |
| **ConfigDict(extra="ignore")** | 忽略模型多余的字段，防止报错 |
| **model_validate_json()** | 从 JSON 字符串校验并实例化 |
| **model_dump_json()** | 序列化为 JSON（支持中文） |
| **结构化输出** | 强制 LLM 输出合规 JSON |

## 文件结构
04_financial_extraction/
├── main.py # 主程序
└── README.md # 本说明文档

## 运行

```bash
cd week1_rag_base/04_financial_extraction
python main.py
