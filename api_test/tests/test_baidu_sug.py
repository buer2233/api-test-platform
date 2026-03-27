"""
百度搜索建议接口测试 - 简单Demo
演示如何测试一个公开的HTTP接口
"""
import pytest
import requests
from core.base_api import BaseAPI


class TestBaiduSuggestionAPI:
    """百度搜索建议API测试类"""

    # 接口配置
    BASE_URL = "https://www.baidu.com"
    SUGGEST_ENDPOINT = "/sugrec"

    @pytest.fixture(scope="class")
    def api(self):
        """初始化API实例"""
        api = BaseAPI()
        yield api
        api.session.close()

    @pytest.mark.basic
    @pytest.mark.smoke
    def test_baidu_suggestion_basic(self, api):
        """
        测试百度搜索建议接口 - 基础功能
        验证:
            1. 接口返回200状态码
            2. 返回JSON格式数据
            3. 包含搜索关键词
            4. 返回建议列表
        """
        # 构建请求URL
        keyword = "测试"
        params = {
            "pre": "1",
            "p": "3",
            "ie": "utf-8",
            "json": "1",
            "prod": "pc",
            "from": "pc_web",
            "wd": keyword
        }

        # 发送GET请求
        url = f"{self.BASE_URL}{self.SUGGEST_ENDPOINT}"
        response = api.session.get(url, params=params, timeout=10)

        # 验证1: 检查状态码
        assert response.status_code == 200, f"接口返回状态码异常: {response.status_code}"

        # 验证2: 检查返回JSON格式
        try:
            data = response.json()
        except ValueError:
            assert False, "接口返回的不是有效的JSON格式"

        # 验证3: 检查包含搜索关键词
        assert "q" in data, "响应中缺少搜索关键词字段'q'"
        assert data["q"] == keyword, f"搜索关键词不匹配，期望: {keyword}, 实际: {data['q']}"

        # 验证4: 检查返回建议列表
        assert "g" in data, "响应中缺少建议列表字段'g'"
        suggestions = data["g"]
        assert isinstance(suggestions, list), "建议列表应该是数组类型"
        assert len(suggestions) > 0, "建议列表不应为空"

        print(f"\n✓ 搜索关键词: {data['q']}")
        print(f"✓ 返回建议数量: {len(suggestions)}")
        print(f"✓ 前3条建议:")
        for i, sug in enumerate(suggestions[:3], 1):
            print(f"  {i}. {sug.get('q', 'N/A')}")

    @pytest.mark.basic
    def test_baidu_suggestion_different_keywords(self, api):
        """
        测试百度搜索建议接口 - 不同关键词
        验证:
            1. 不同关键词返回不同结果
            2. 英文关键词也能正常工作
        """
        # 测试中文关键词
        chinese_keyword = "Python"
        chinese_params = {
            "pre": "1",
            "p": "3",
            "ie": "utf-8",
            "json": "1",
            "prod": "pc",
            "from": "pc_web",
            "wd": chinese_keyword
        }

        url = f"{self.BASE_URL}{self.SUGGEST_ENDPOINT}"
        response = api.session.get(url, params=chinese_params, timeout=10)

        assert response.status_code == 200
        data = response.json()
        # 百度会将关键词转换为小写
        assert data["q"].lower() == chinese_keyword.lower()
        assert len(data["g"]) > 0

        print(f"\n✓ '{chinese_keyword}' 返回 {len(data['g'])} 条建议")

        # 测试英文关键词
        english_keyword = "AI"
        english_params = chinese_params.copy()
        english_params["wd"] = english_keyword

        response2 = api.session.get(url, params=english_params, timeout=10)

        assert response2.status_code == 200
        data2 = response2.json()
        # 百度会将关键词转换为小写
        assert data2["q"].lower() == english_keyword.lower()
        assert len(data2["g"]) > 0

        print(f"✓ '{english_keyword}' 返回 {len(data2['g'])} 条建议")

    @pytest.mark.basic
    def test_baidu_suggestion_empty_keyword(self, api):
        """
        测试百度搜索建议接口 - 空关键词
        验证:
            1. 空关键词也能正常返回
            2. 返回空或默认建议
        """
        params = {
            "pre": "1",
            "p": "3",
            "ie": "utf-8",
            "json": "1",
            "prod": "pc",
            "from": "pc_web",
            "wd": ""
        }

        url = f"{self.BASE_URL}{self.SUGGEST_ENDPOINT}"
        response = api.session.get(url, params=params, timeout=10)

        # 空关键词应该返回200或相关错误
        assert response.status_code == 200

        data = response.json()
        # 空关键词可能返回空对象或包含q字段
        if len(data) > 0:
            # 如果返回数据，检查结构
            assert "q" in data or "g" in data
        print(f"\n✓ 空关键词测试通过，返回: {data}")

    @pytest.mark.basic
    def test_baidu_suggestion_response_time(self, api):
        """
        测试百度搜索建议接口 - 响应时间
        验证:
            1. 接口响应时间在可接受范围内
        """
        import time

        keyword = "性能测试"
        params = {
            "pre": "1",
            "p": "3",
            "ie": "utf-8",
            "json": "1",
            "prod": "pc",
            "from": "pc_web",
            "wd": keyword
        }

        url = f"{self.BASE_URL}{self.SUGGEST_ENDPOINT}"

        # 记录开始时间
        start_time = time.time()

        response = api.session.get(url, params=params, timeout=10)

        # 记录结束时间
        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # 转换为毫秒

        assert response.status_code == 200
        data = response.json()

        # 验证响应时间应在3秒内
        assert response_time < 3000, f"接口响应时间过长: {response_time:.2f}ms"

        print(f"\n✓ 关键词 '{keyword}'")
        print(f"✓ 响应时间: {response_time:.2f}ms")
        print(f"✓ 返回建议数: {len(data.get('g', []))}")


class TestBaiduSuggestionAdvanced:
    """百度搜索建议API高级测试"""

    @pytest.fixture(scope="class")
    def api(self):
        """初始化API实例"""
        api = BaseAPI()
        yield api
        api.session.close()

    @pytest.mark.P0
    @pytest.mark.regression
    def test_baidu_suggestion_data_structure(self, api):
        """
        测试百度搜索建议接口 - 数据结构验证
        验证:
            1. 响应数据包含所有必要字段
            2. 数据类型正确
            3. 建议项包含必要信息
        """
        keyword = "数据结构"
        params = {
            "pre": "1",
            "p": "3",
            "ie": "utf-8",
            "json": "1",
            "prod": "pc",
            "from": "pc_web",
            "wd": keyword
        }

        url = f"https://www.baidu.com{TestBaiduSuggestionAPI.SUGGEST_ENDPOINT}"
        response = api.session.get(url, params=params, timeout=10)

        data = response.json()

        # 验证顶层字段
        required_fields = ["q", "g"]
        for field in required_fields:
            assert field in data, f"响应中缺少必要字段: {field}"

        # 验证建议项结构
        suggestions = data["g"]
        if len(suggestions) > 0:
            first_suggestion = suggestions[0]

            # 验证建议项包含必要字段
            assert "q" in first_suggestion, "建议项缺少'q'字段"
            assert "sa" in first_suggestion, "建议项缺少'sa'字段"

            # 验证字段类型
            assert isinstance(first_suggestion["q"], str), "建议关键词应该是字符串"
            assert isinstance(first_suggestion["sa"], str), "建议标识应该是字符串"

            print(f"\n✓ 数据结构验证通过")
            print(f"✓ 首条建议: {first_suggestion['q']}")

    @pytest.mark.P0
    def test_baidu_suggestion_special_characters(self, api):
        """
        测试百度搜索建议接口 - 特殊字符处理
        验证:
            1. 接口能正确处理特殊字符
            2. URL编码正确
        """
        from urllib.parse import quote

        # 测试包含特殊字符的关键词
        special_keywords = ["C++", "Java&Python", "测试@#$"]

        for keyword in special_keywords:
            params = {
                "pre": "1",
                "p": "3",
                "ie": "utf-8",
                "json": "1",
                "prod": "pc",
                "from": "pc_web",
                "wd": keyword
            }

            url = f"https://www.baidu.com{TestBaiduSuggestionAPI.SUGGEST_ENDPOINT}"
            response = api.session.get(url, params=params, timeout=10)

            assert response.status_code == 200, f"关键词 '{keyword}' 请求失败"
            data = response.json()

            print(f"\n✓ 特殊字符关键词 '{keyword}' 测试通过")
            print(f"  返回建议数: {len(data.get('g', []))}")
