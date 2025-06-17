import pytest
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from dash.testing.application_runners import import_app

def pytest_addoption(parser):
    """为pytest添加自定义命令行选项"""
    # 不再添加自己的--headless选项，因为dash-testing已经提供了
    pass

# dash-testing已经提供了内置的无头模式支持
# 使用 pytest --headless 来启用无头模式
# 这是dash-testing官方推荐的方式 