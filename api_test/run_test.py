"""
测试运行脚本
提供便捷的测试运行方式
"""
import argparse
import os
import sys
import subprocess


def build_pytest_command(args):
    """根据参数构建 pytest 命令。"""
    cmd = ['pytest', '-vv' if args.verbose else '-v']
    marker_expression = args.mark

    if args.public_baseline:
        public_expression = 'not private_env'
        marker_expression = f"({marker_expression}) and {public_expression}" if marker_expression else public_expression

    if marker_expression:
        cmd.extend(['-m', marker_expression])

    if args.file:
        cmd.append(args.file)

    if args.html:
        report_dir = 'report'
        if not os.path.exists(report_dir):
            os.makedirs(report_dir)
        cmd.extend(['--html', f'{report_dir}/report.html', '--self-contained-html'])

    if args.reruns:
        cmd.extend(['--reruns', str(args.reruns)])

    return cmd


def run_pytest(args):
    """运行pytest测试"""
    cmd = build_pytest_command(args)

    print(f"执行命令: {' '.join(cmd)}")

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
    parser.add_argument(
        '--public-baseline',
        action='store_true',
        help='排除 private_env 标记，用于本地公开回归基线'
    )

    args = parser.parse_args()

    # 运行测试
    return_code = run_pytest(args)

    sys.exit(return_code)


if __name__ == '__main__':
    main()
