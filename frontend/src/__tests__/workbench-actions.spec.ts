import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import WorkbenchView from '../views/WorkbenchView.vue'


function createJsonResponse(payload: unknown): Response {
  return new Response(JSON.stringify(payload), {
    status: 200,
    headers: {
      'Content-Type': 'application/json'
    }
  })
}


describe('WorkbenchView 执行动作', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('点击执行与失败重试按钮会调用后端接口', async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input)
      if (url.endsWith('/api/v2/workbench/bootstrap/')) {
        return Promise.resolve(
          createJsonResponse({
            success: true,
            data: {
              page_title: '抓包与接口自动化工作台',
              frontend_framework: 'vue3',
              frontend_entry: '/ui/v3/workbench/',
              design_source: 'DESIGN.md'
            }
          })
        )
      }
      if (url.endsWith('/api/v2/workbench/navigation/')) {
        return Promise.resolve(
          createJsonResponse({
            success: true,
            data: {
              projects: [
                {
                  project_code: 'demo-project',
                  project_name: '示例项目',
                  modules: [
                    {
                      module_code: 'account_center',
                      module_name: '账号中心',
                      submodules: [
                          {
                            submodule_code: 'profile_management',
                            submodule_name: '资料管理',
                            testcases: [
                              {
                              scenario_id: 'scenario-001',
                              scenario_code: 'query_user_profile',
                              scenario_name: '查询用户资料',
                                review_status: 'approved',
                                execution_status: 'failed'
                              }
                            ],
                            test_interfaces: [
                              {
                                interface_id: 'interface-01',
                                method_name: 'get_user_01',
                                http_method: 'GET',
                                path_template: '/users/01'
                              }
                            ]
                          }
                        ]
                      }
                    ]
                  }
              ]
            }
          })
        )
      }
      if (url.endsWith('/api/v2/scenarios/scenario-001/')) {
        return Promise.resolve(
          createJsonResponse({
            success: true,
            data: {
              scenario_id: 'scenario-001',
              scenario_name: '查询用户资料',
              scenario_code: 'query_user_profile',
              review_status: 'approved',
              execution_status: 'failed',
              steps: []
            }
          })
        )
      }
      if (url.endsWith('/api/v2/scenarios/scenario-001/result/')) {
        return Promise.resolve(
          createJsonResponse({
            success: true,
            data: {
              execution_status: 'failed',
              latest_execution_id: 'execution-001',
              passed_count: 0,
              failed_count: 1,
              skipped_count: 0,
              report_path: 'report/allure/index.html',
              latest_allure_report_path: 'report/allure/index.html',
              retry_available: true
            }
          })
        )
      }
      if (url.endsWith('/api/v2/scenarios/scenario-001/execute/')) {
        return Promise.resolve(
          createJsonResponse({
            success: true,
            data: {
              scenario_id: 'scenario-001',
              execution_id: 'execution-002',
              execution_status: 'running'
            }
          })
        )
      }
      return Promise.reject(new Error(`未处理的请求: ${url} ${JSON.stringify(init)}`))
    })

    vi.stubGlobal('fetch', fetchMock)

    const wrapper = mount(WorkbenchView)
    await flushPromises()
    await wrapper.get('[data-testid="testcase-node-scenario-001"]').trigger('click')
    await flushPromises()
    await wrapper.get('[data-testid="execute-testcase-button"]').trigger('click')
    await wrapper.get('[data-testid="retry-failed-testcase-button"]').trigger('click')

    const executeCalls = fetchMock.mock.calls.filter(([input]) =>
      String(input).endsWith('/api/v2/scenarios/scenario-001/execute/')
    )

    expect(executeCalls).toHaveLength(2)
    expect(executeCalls[0]?.[1]).toMatchObject({
      method: 'POST'
    })
    expect(executeCalls[1]?.[1]).toMatchObject({
      method: 'POST'
    })
  })
})
