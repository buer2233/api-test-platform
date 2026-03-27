"""
pytest配置文件 - 提供fixture和钩子函数
"""
import os
import sys
import time
from datetime import datetime
from typing import Tuple, List

import pytest
from py.xml import html

# 添加项目路径到sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import RunConfig


# ==================== 测试账号管理 ====================

def get_test_account(file_name: str = "account.txt") -> Tuple[List[str], List[str], List[str], List[str], List[str]]:
    """
    从文件中读取测试账号信息

    Args:
        file_name: 账号文件名

    Returns:
        (姓名列表, 账号列表, 密码列表, 备注列表, 团队列表)
    """
    test_data_dir = os.path.join(os.path.dirname(__file__), 'test_data')
    file_path = os.path.join(test_data_dir, file_name)

    if not os.path.exists(file_path):
        # 返回默认测试账号
        return (
            ['测试管理员', '测试成员'],
            ['admin@test.com', 'user@test.com'],
            ['Test123456', 'Test123456'],
            ['管理员', '普通成员'],
            ['测试团队', '测试团队']
        )

    names = []
    usernames = []
    passwords = []
    remarks = []
    teams = []

    with open(file_path, 'r', encoding='UTF-8') as f:
        for line in f:
            parts = line.strip().split(',')
            if len(parts) >= 3:
                names.append(parts[0].strip())
                usernames.append(parts[1].strip())
                passwords.append(parts[2].strip())
                remarks.append(parts[3].strip() if len(parts) > 3 else '')
                teams.append(parts[4].strip() if len(parts) > 4 else '')

    return names, usernames, passwords, remarks, teams


# 获取测试账号数据
_ACCOUNT_NAMES, _ACCOUNT_USERNAMES, _ACCOUNT_PASSWORDS, _ACCOUNT_REMARKS, _ACCOUNT_TEAMS = get_test_account()


# ==================== Fixtures ====================

@pytest.fixture(scope="session")
def test_accounts():
    """获取所有测试账号"""
    return {
        'names': _ACCOUNT_NAMES,
        'usernames': _ACCOUNT_USERNAMES,
        'passwords': _ACCOUNT_PASSWORDS,
        'remarks': _ACCOUNT_REMARKS,
        'teams': _ACCOUNT_TEAMS
    }


@pytest.fixture(scope="session")
def admin_account(test_accounts):
    """获取管理员账号"""
    return {
        'name': test_accounts['names'][0],
        'username': test_accounts['usernames'][0],
        'password': test_accounts['passwords'][0],
        'team': test_accounts['teams'][0]
    }


@pytest.fixture(scope="session")
def employee_account(test_accounts):
    """获取普通成员账号"""
    if len(test_accounts['names']) > 1:
        return {
            'name': test_accounts['names'][1],
            'username': test_accounts['usernames'][1],
            'password': test_accounts['passwords'][1],
            'team': test_accounts['teams'][1]
        }
    return admin_account


@pytest.fixture(scope="function")
def base_url():
    """获取测试环境URL"""
    protocol = 'https://' if RunConfig.IS_HTTPS else 'http://'
    return protocol + RunConfig.BASE_URL


# ==================== pytest钩子函数 ====================

@pytest.fixture(autouse=True)
def test_description(request):
    """为测试用例添加描述信息"""
    if hasattr(request.node, '_obj'):
        description = request.node._obj.__doc__ or "未提供用例描述"
    else:
        description = "未提供用例描述"

    # 设置环境变量供其他地方使用
    os.environ['node_id'] = request.node.nodeid
    os.environ['case_description'] = description

    yield

    # 清理环境变量
    os.environ.pop('node_id', None)
    os.environ.pop('case_description', None)


def pytest_configure(config):
    """pytest配置钩子"""
    # 可以在这里添加一些初始化操作
    pass


@pytest.mark.optionalhook
def pytest_html_results_summary(prefix, summary, postfix):
    """自定义HTML测试报告摘要"""
    protocol = 'https://' if RunConfig.IS_HTTPS else 'http://'
    base_url = protocol + RunConfig.BASE_URL

    # 添加测试环境信息
    prefix.extend([html.p(f"测试环境: {base_url}")])

    # 添加测试时间
    test_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    prefix.extend([html.p(f"测试时间: {test_time}")])

    # 计算通过率
    passed = summary[3] if len(summary) > 3 else 0
    failed = summary[9] if len(summary) > 9 else 0
    error = summary[12] if len(summary) > 12 else 0

    # 从summary对象中提取数值
    import re
    def extract_number(s):
        match = re.search(r'\d+', str(s))
        return int(match.group()) if match else 0

    passed_num = extract_number(passed)
    failed_num = extract_number(failed)
    error_num = extract_number(error)
    total = passed_num + failed_num + error_num

    if total > 0:
        pass_rate = (passed_num / total) * 100
        prefix.extend([html.h2(f"测试通过率: {pass_rate:.2f}%")])


@pytest.mark.optionalhook
def pytest_html_results_table_header(cells):
    """自定义HTML测试报告表头"""
    cells.insert(1, html.th('描述'))
    cells.insert(2, html.th('用例ID'))
    cells.insert(3, html.th('状态'))


@pytest.mark.optionalhook
def pytest_html_results_table_row(report, cells):
    """自定义HTML测试报告表格行"""
    # 添加用例描述
    try:
        description = getattr(report, 'description', '') or str(report.nodeid)
    except:
        description = report.nodeid

    cells.insert(1, html.td(description))
    cells.insert(2, html.td(report.nodeid))

    # 添加状态标识
    if report.passed:
        status = '<span style="color:green">通过</span>'
    elif report.failed:
        status = '<span style="color:red">失败</span>'
    else:
        status = '<span style="color:orange">跳过</span>'

    cells.insert(3, html.td(status))


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    """生成测试报告时的钩子"""
    outcome = yield
    report = outcome.get_result()

    # 添加用例描述
    if hasattr(item, 'function'):
        report.description = item.function.__doc__ or "未提供用例描述"
    else:
        report.description = "未提供用例描述"

    # 处理失败用例
    if call.when == 'call' and report.failed:
        # 可以在这里添加失败截图或其他处理
        pass


@pytest.mark.optionalhook
def pytest_html_results_table_html(report, data):
    """删除通过用例的详细日志"""
    if report.passed:
        data[:] = [html.div('测试通过，无详细日志', class_='empty log')]
