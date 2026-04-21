export interface WorkbenchBootstrap {
  page_title: string
  frontend_framework: string
  frontend_entry: string
  design_source: string
}

export interface WorkbenchTestcaseSummary {
  scenario_id: string
  scenario_code: string
  scenario_name: string
  review_status: string
  execution_status: string
}

export interface WorkbenchTestInterfaceSummary {
  interface_id: string
  method_name: string
  http_method: string
  path_template: string
}

export interface WorkbenchTestInterfaceDetail extends WorkbenchTestInterfaceSummary {
  source_file?: string
  referenced_by?: string[]
}

export interface WorkbenchSubmoduleNode {
  submodule_code: string
  submodule_name: string
  testcases: WorkbenchTestcaseSummary[]
  test_interfaces: WorkbenchTestInterfaceSummary[]
}

export interface WorkbenchModuleNode {
  module_code: string
  module_name: string
  submodules: WorkbenchSubmoduleNode[]
}

export interface WorkbenchProjectNode {
  project_code: string
  project_name: string
  modules: WorkbenchModuleNode[]
}

export interface WorkbenchNavigationPayload {
  projects: WorkbenchProjectNode[]
}

export interface ScenarioStepSummary {
  step_id: string
  step_name: string
  operation_id: string
}

export interface ScenarioDetailPayload {
  scenario_id: string
  scenario_name: string
  scenario_code: string
  review_status: string
  execution_status: string
  steps: ScenarioStepSummary[]
}

export interface ScenarioResultPayload {
  execution_status: string
  latest_execution_id: string
  passed_count: number
  failed_count: number
  skipped_count: number
  report_path: string
  latest_allure_report_path: string
  retry_available: boolean
}

export type WorkbenchMiddleView = 'modules' | 'submodules' | 'testcases' | 'interfaces'
