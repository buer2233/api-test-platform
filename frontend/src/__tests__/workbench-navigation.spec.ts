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


function buildInterfaceItems(count: number) {
  return Array.from({ length: count }, (_, index) => {
    const sequence = String(index + 1).padStart(2, '0')
    return {
      interface_id: `interface-${sequence}`,
      method_name: `get_user_${sequence}`,
      http_method: 'GET',
      path_template: `/users/${sequence}`
    }
  })
}


describe('WorkbenchView 导航树', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('项目、模块、子模块可点击，测试接口列表支持分页并可切换详情', async () => {
    const interfaces = buildInterfaceItems(12)
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
                            test_interfaces: interfaces
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
        if (url.endsWith('/api/v2/workbench/test-interfaces/interface-11/')) {
          return Promise.resolve(
            createJsonResponse({
              success: true,
              data: {
                interface_id: 'interface-11',
                method_name: 'get_user_11',
                http_method: 'GET',
                path_template: '/users/11',
                source_file: 'api_test/core/jsonplaceholder_api.py',
                referenced_by: ['api_test/tests/jsonplaceholder/test_get_user_11.py']
              }
            })
          )
        }
        return Promise.reject(new Error(`未处理的请求: ${url}`))
      })
    )

    const wrapper = mount(WorkbenchView)
    await flushPromises()

    expect(wrapper.get('[data-testid="project-node-demo-project"]').text()).toContain('示例项目')
    expect(wrapper.get('[data-testid="module-node-account_center"]').text()).toContain('账号中心')
    expect(wrapper.get('[data-testid="submodule-node-profile_management"]').text()).toContain('资料管理')
    expect(wrapper.get('[data-testid="middle-panel-title"]').text()).toContain('测试用例')
    expect(wrapper.text()).toContain('查询用户资料')

    await wrapper.get('[data-testid="tree-switch-interfaces"]').trigger('click')
    await flushPromises()

    expect(wrapper.get('[data-testid="middle-panel-title"]').text()).toContain('测试接口')
    expect(wrapper.text()).toContain('get_user_01')
    expect(wrapper.text()).not.toContain('get_user_11')
    expect(wrapper.get('[data-testid="pagination-indicator"]').text()).toBe('1 / 2')

    await wrapper.get('[data-testid="pagination-next"]').trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('get_user_11')
    expect(wrapper.get('[data-testid="pagination-indicator"]').text()).toBe('2 / 2')

    await wrapper.get('[data-testid="middle-item-interface-interface-11"]').trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('/users/11')
    expect(wrapper.text()).toContain('api_test/core/jsonplaceholder_api.py')
  })
})
