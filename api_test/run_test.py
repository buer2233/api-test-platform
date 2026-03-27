"""
测试运行脚本
提供便捷的测试运行方式
"""
import argparse
import os
import sys
import subprocess


def run_pytest(args):
    """运行pytest测试"""

    # 构建pytest命令
    cmd = ['pytest', '-v']

    # 添加标记
    if args.mark:
        cmd.extend(['-m', args.mark])

    # 添加文件
    if args.file:
        cmd.append(args.file)

    # 添加HTML报告
    if args.html:
        report_dir = 'report'
        if not os.path.exists(report_dir):
            os.makedirs(report_dir)
        cmd.extend(['--html', f'{report_dir}/report.html', '--self-contained-html'])

    # 添加重跑
    if args.reruns:
        cmd.extend(['--reruns', str(args.reruns)])

    # 添加详细输出
    if args.verbose:
        cmd.append('-vv')
    else:
        cmd.append('-v')

    print(f"执行命令: {' '.join(cmd)}")

    # 执行测试
    result = subprocess.run(cmd)
    return result.returncode


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='接口自动化测试运行器')

    parser.add_argument(
        '-m', '--mark',
        help='按标记运行测试 (如: smoke, basic, P0)'
    )
    parser.add_argument(
        '-f', '--file',
        help='运行指定测试文件'
    )
    parser.add_argument(
        '--html',
        action='store_true',
        help='生成HTML测试报告'
    )
    parser.add_argument(
        '--reruns',
        type=int,
        default=0,
        help='失败重跑次数'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='更详细的输出'
    )

    args = parser.parse_args()

    # 运行测试
    return_code = run_pytest(args)

    sys.exit(return_code)


if __name__ == '__main__':
    main()
