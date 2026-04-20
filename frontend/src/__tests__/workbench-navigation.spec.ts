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


describe('WorkbenchView 导航树', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('渲染项目-模块-子模块-测试用例-测试接口导航树并切换详情', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn((input: RequestInfo | URL) => {
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
                                execution_status: 'passed'
                              }
                            ],
                            test_interfaces: [
                              {
                                interface_id: 'shared__common__JsonPlaceholderAPI__get_user',
                                method_name: 'get_user',
                                http_method: 'GET',
                                path_template: '/users/{user_id}'
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
                execution_status: 'passed',
                steps: [
                  {
                    step_id: 'step-001',
                    step_name: '查询用户详情',
                    operation_id: 'operation-get-user'
                  }
                ]
              }
            })
          )
        }
        if (url.endsWith('/api/v2/scenarios/scenario-001/result/')) {
          return Promise.resolve(
            createJsonResponse({
              success: true,
              data: {
                execution_status: 'passed',
                latest_execution_id: 'execution-001',
                passed_count: 1,
                failed_count: 0,
                skipped_count: 0,
                report_path: 'report/allure/index.html',
                latest_allure_report_path: 'report/allure/index.html',
                retry_available: false
              }
            })
          )
        }
        return Promise.reject(new Error(`未处理的请求: ${url}`))
      })
    )

    const wrapper = mount(WorkbenchView)
    await flushPromises()

    expect(wrapper.text()).toContain('示例项目')
    expect(wrapper.text()).toContain('账号中心')
    expect(wrapper.text()).toContain('资料管理')
    expect(wrapper.text()).toContain('查询用户资料')
    expect(wrapper.text()).toContain('get_user')

    await wrapper.get('[data-testid="testcase-node-scenario-001"]').trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('query_user_profile')
    expect(wrapper.text()).toContain('execution-001')
    expect(wrapper.text()).toContain('report/allure/index.html')
  })
})
