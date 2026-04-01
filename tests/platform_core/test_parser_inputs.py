"""解析器输入格式测试。"""

from pathlib import Path

from platform_core.parsers import OpenAPIDocumentParser


def test_parser_supports_yaml_openapi_documents(tmp_path):
    """解析器应支持 YAML 格式的 OpenAPI 文档。"""
    source_path = tmp_path / "user_openapi.yaml"
    source_path.write_text(
        """
openapi: 3.0.0
info:
  title: User API
  version: 1.0.0
paths:
  /api/users/{user_id}:
    get:
      tags: [user]
      operationId: getUserProfile
      summary: 获取用户详情
      parameters:
        - name: user_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: success
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    type: object
                    properties:
                      id:
                        type: string
                        example: u-100
""".strip(),
        encoding="utf-8",
    )

    parsed = OpenAPIDocumentParser().parse(source_path)

    assert parsed.source_document.source_type == "openapi"
    assert len(parsed.operations) == 1
    assert parsed.operations[0].operation_code == "get_user_profile"


def test_parser_supports_yaml_swagger_documents_with_multiple_operations(tmp_path):
    """解析器应支持 Swagger YAML 并解析多个接口。"""
    source_path = tmp_path / "user_swagger.yml"
    source_path.write_text(
        """
swagger: '2.0'
info:
  title: User API
  version: 1.0.0
paths:
  /api/users:
    get:
      tags: [user]
      operationId: listUsers
      summary: 查询用户列表
      responses:
        '200':
          description: success
          schema:
            type: object
            properties:
              data:
                type: array
    post:
      tags: [user]
      operationId: createUser
      summary: 创建用户
      parameters:
        - name: body
          in: body
          required: true
          schema:
            type: object
            required: [name]
            properties:
              name:
                type: string
      responses:
        '201':
          description: created
          schema:
            type: object
            properties:
              data:
                type: object
                properties:
                  id:
                    type: string
""".strip(),
        encoding="utf-8",
    )

    parsed = OpenAPIDocumentParser().parse(source_path)

    assert parsed.source_document.source_type == "swagger"
    assert {operation.operation_code for operation in parsed.operations} == {"list_users", "create_user"}
    assert any(operation.http_method == "POST" for operation in parsed.operations)
