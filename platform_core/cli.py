from __future__ import annotations

import argparse
import json
from pathlib import Path

from platform_core.pipeline import DocumentDrivenPipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="platform_core CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="执行文档驱动最小闭环")
    run_parser.add_argument("--source", required=True, help="OpenAPI/Swagger 文档路径")
    run_parser.add_argument("--output", required=True, help="输出工作目录")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "run":
        pipeline = DocumentDrivenPipeline(project_root=Path.cwd())
        result = pipeline.run(source_path=args.source, output_root=args.output)
        print(
            json.dumps(
                {
                    "source": result.source_document.source_name,
                    "modules": len(result.modules),
                    "operations": len(result.operations),
                    "execution_target": result.execution_record.target_id,
                    "execution_status": result.execution_record.result_status,
                    "report_path": result.execution_record.report_path,
                },
                ensure_ascii=False,
            )
        )
        return 0 if result.execution_record.result_status == "passed" else 1

    parser.error("unsupported command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
