# -*- coding: utf-8 -*-
"""stock_server.py 单元测试 —— 财报雷达升级包第①步
四个用例对应任务清单：正常路径 / 降级分支 / 重试逻辑 / 错误兜底
原则：mock 隔离外部依赖（akshare），测试不连真网、结果可控"""
from unittest.mock import patch
import pandas as pd
from stock_server import get_stock_code, get_realtime_quote, get_stock_history


# ---------- 假数据工厂（Arrange 的材料） ----------

def fake_bid_ask():
    """假实时行情：列名和 akshare 东财接口一致（item/value 两列）"""
    return pd.DataFrame({
        "item": ["最新", "涨跌", "涨幅", "今开", "最高", "最低"],
        "value": ["25.30", "+0.50", "2.02", "24.90", "25.80", "24.70"],
    })


def fake_hist():
    """假日K：列名和 stock_zh_a_hist 一致（代码里 r['日期'] 直接取列名）"""
    return pd.DataFrame({
        "日期": ["2026-10-29"],
        "收盘": [25.30],
        "开盘": [24.90],
        "最高": [25.80],
        "最低": [24.70],
        "涨跌幅": [2.02],
    })


# ---------- ① 正常路径 ----------

def test_get_stock_code_正常路径():
    """映射表直查（纯函数，无需 mock）：三家公司全对 + 未收录提示"""
    assert get_stock_code("工业富联") == "601138"
    assert get_stock_code("紫金矿业") == "601899"
    assert get_stock_code("兴业银行") == "601166"
    assert "未收录" in get_stock_code("不存在的公司")


def test_get_realtime_quote_正常路径():
    """实时源正常：mock akshare 喂假数据，断言输出含最新价和（实时源）标记"""
    with patch("stock_server.ak.stock_bid_ask_em", return_value=fake_bid_ask()):
        out = get_realtime_quote("601138")
    assert "最新价 25.30" in out
    assert "（实时源）" in out


# ---------- ② 降级分支 ----------

def test_get_realtime_quote_降级到日K():
    """实时源抛异常 → 自动降级日K：断言输出含（降级源：日K）标记
    注意：side_effect 抛异常会让 _retry 重试 2 次，必须 patch time.sleep，
    否则测试真的等 1.5 秒 × 2"""
    with patch("stock_server.ak.stock_bid_ask_em", side_effect=Exception("实时源断连")), \
         patch("stock_server.ak.stock_zh_a_hist", return_value=fake_hist()), \
         patch("stock_server.time.sleep"):
        out = get_realtime_quote("601138")
    assert "降级源：日K" in out
    assert "最新交易日 2026-10-29" in out
    assert "收 25.3" in out   # float 25.30 经 f-string 格式化显示为 25.3


# ---------- ③ 重试逻辑 ----------

def test_get_stock_history_重试后成功():
    """第一次调用抛异常、第二次成功：断言重试后正常返回，且真的调了 2 次"""
    with patch("stock_server.ak.stock_zh_a_hist",
               side_effect=[Exception("第一次失败"), fake_hist()]) as mock_hist, \
         patch("stock_server.time.sleep") as mock_sleep:
        out = get_stock_history("601138")
    assert "2026-10-29" in out          # 重试后正常返回
    assert mock_hist.call_count == 2    # 证明真的重试了（第 1 次挂、第 2 次成）
    assert mock_sleep.call_count == 1   # 失败一次 → sleep 一次


# ---------- ④ 错误兜底 ----------

def test_get_realtime_quote_全挂兜底():
    """实时源和日K都抛异常：断言返回「暂时不可用」提示，不抛裸异常"""
    with patch("stock_server.ak.stock_bid_ask_em", side_effect=Exception("实时源断连")), \
         patch("stock_server.ak.stock_zh_a_hist", side_effect=Exception("日K也断连")), \
         patch("stock_server.time.sleep"):
        out = get_realtime_quote("601138")
    assert out.startswith("行情接口暂时不可用")


def test_get_stock_history_全挂兜底():
    """日K接口抛异常：断言返回「暂时不可用」提示"""
    with patch("stock_server.ak.stock_zh_a_hist", side_effect=Exception("日K断连")), \
         patch("stock_server.time.sleep"):
        out = get_stock_history("601138")
    assert out.startswith("行情接口暂时不可用")
