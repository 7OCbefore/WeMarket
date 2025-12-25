#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信市场情报自动化系统 (WMIS)
WeChat Market Intelligence System

入口文件
"""

from src.pipeline import ETLPipeline


def main():
    """主入口"""
    pipeline = ETLPipeline("./config.yaml")
    pipeline.run()


if __name__ == "__main__":
    main()
