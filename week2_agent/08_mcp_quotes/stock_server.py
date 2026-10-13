# 08号：自写行情 MCP server（三大亮点③）
# 把 akshare 的行情能力包装成 MCP 工具，供 Agent 通过 MCP 协议调用

from datetime import date, timedelta
import time
import akshare as ak
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("股票行情服务")

# 三家公司：财报知识库里的主角，代码写死在映射表里（确定性计算，不靠大模型）
COMPANY_CODES = {
    "工业富联": "601138",
    "紫金矿业": "601899",
    "兴业银行": "601166",
}

def _recent_range(days=45):
    """最近 N 天的日期区间（YYYYMMDD 格式），作为日K查询的默认范围"""
    end = date.today().strftime("%Y%m%d")
    start = (date.today() - timedelta(days=days)).strftime("%Y%m%d")
    return start, end

def _retry(func, *args, retries=2, wait=1.5, **kwargs):
    """网络接口重试：东财接口偶发断连（限流/网络波动），重试几次往往就好"""
    for i in range(retries):
        try:
            return func(*args, **kwargs)
        except Exception:
            if i == retries - 1:
                raise
            time.sleep(wait)

@mcp.tool()
def get_stock_code(company_name: str) -> str:
    """公司名→股票代码。
    何时使用：Agent 拿到公司名称（如'工业富联'）要查行情时，先用本工具换成代码。
    参数：company_name 公司简称（工业富联/紫金矿业/兴业银行）
    返回：6位股票代码，如 601138"""
    return COMPANY_CODES.get(company_name, "未收录该公司，支持：工业富联/紫金矿业/兴业银行")

@mcp.tool()
def get_realtime_quote(stock_code: str) -> str:
    """查询最新行情（带自动降级）。
    何时使用：需要某只股票当前的最新价、涨跌幅时使用。
    参数：stock_code 6位股票代码，如'601138'
    返回：最新价、涨跌、今开、最高、最低；若实时源被断连则自动降级为日K最新交易日数据"""
    try:
        df = _retry(ak.stock_bid_ask_em, symbol=stock_code)
        kv = dict(zip(df["item"], df["value"]))
        return (f"{stock_code} 最新价 {kv.get('最新')} 元，"
                f"涨跌 {kv.get('涨跌')} 元（{kv.get('涨幅')}%），"
                f"今开 {kv.get('今开')}，最高 {kv.get('最高')}，最低 {kv.get('最低')}（实时源）")
    except Exception:
        try:
            # 降级：东财实时接口偶发断连（限流/网络波动），改用日K接口兜底
            # 交易时段内，日K最后一根就是当天实时更新的 bar
            start, end = _recent_range()
            df = _retry(ak.stock_zh_a_hist, symbol=stock_code, period="daily",
                        start_date=start, end_date=end, adjust="")
            r = df.iloc[-1]
            return (f"{stock_code} 最新交易日 {r['日期']}：收 {r['收盘']}，"
                    f"开 {r['开盘']}，最高 {r['最高']}，最低 {r['最低']}，"
                    f"涨跌幅 {r['涨跌幅']}%（降级源：日K）")
        except Exception as e:
            return f"行情接口暂时不可用（{type(e).__name__}），请稍后再试"

@mcp.tool()
def get_stock_history(stock_code: str, start_date: str = "", end_date: str = "") -> str:
    """查询日K历史行情。
    何时使用：需要看某只股票一段时间的走势（如'财报发布后股价怎么走的'）时使用。
    参数：stock_code 6位股票代码；start_date/end_date 起止日期（YYYYMMDD格式，不填则默认最近45天）
    返回：最近10个交易日的 日期/开盘/收盘/涨跌幅 摘要"""
    try:
        if not start_date or not end_date:
            start_date, end_date = _recent_range()
        df = _retry(ak.stock_zh_a_hist, symbol=stock_code, period="daily",
                    start_date=start_date, end_date=end_date, adjust="qfq")
        if df.empty:
            return "该区间无数据（可能是非交易日或日期范围无效）"
        lines = [f"{r['日期']}: 开{r['开盘']} 收{r['收盘']} 涨跌幅{r['涨跌幅']}%"
                 for _, r in df.tail(10).iterrows()]
        return "\n".join(lines)
    except Exception as e:
        return f"行情接口暂时不可用（{type(e).__name__}），请稍后再试"

if __name__ == "__main__":
    mcp.run()  # stdio 传输：MCP 客户端（我们的 Agent）会启动本脚本并与之通信
