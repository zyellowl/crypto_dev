# Crypto Twitter LLM Signal

本项目用于自动抓取推特（Twitter）相关内容，聚合后交由大模型（LLM，如DeepSeek）分析，对指定币种给出买入/卖出/观望建议。

## 功能简介
- 支持通过 Nitter RSS 和 RSSHub 聚合推特内容
- 自动组装所有推文为大prompt，调用LLM分析情绪与影响力
- 输出针对币种的操作建议（买入/卖出/观望）

## 目录结构
```
crypto_quant_project/
├── main_twitter_llm.py           # 主程序入口
├── rsshub_twitter_fetcher.py     # RSSHub推特内容抓取模块
├── core/
│   ├── resource_fetcher.py       # 信息抓取统一接口
│   └── llm_analyzer.py           # LLM分析模块
├── config.ini                    # 配置文件（需自行填写API密钥等）
├── requirements.txt              # 依赖包列表
└── .gitignore                    # Git忽略文件
```

## 安装依赖
建议使用Python 3.8+，并在虚拟环境下安装：
```bash
pip install -r requirements.txt
```

## 配置说明
1. 复制 `config.ini` 并填写：
   - LLM API Key（如DeepSeek）
   - [Nitter] 下配置要监控的推特用户名
   - [Trading] 下配置币种（如BTC/USDT）
2. 如需本地RSSHub，确保 `http://localhost:1200/twitter/home_latest` 可访问

## 运行方法
```bash
python main_twitter_llm.py
```

## 输出示例
```
抓取推特内容并分析 BTC/USDT 的操作建议...
共聚合 20 条推文内容。
[LLM Prompt Preview]
请根据以下所有推特内容，判断对BTC/USDT的操作建议（买入/卖出/观望），并简要说明理由：
...
LLM情绪分: 0.35，置信度: 0.92

【最终建议】BTC/USDT: BUY
```

## 注意事项
- 本项目仅供技术交流与研究，投资决策请谨慎！
- 若需扩展数据源、分析模板或自动化交易，可在此基础上开发。

---
如有问题或建议，欢迎提issue或联系作者。 