import type {
  ScenarioDetailPayload,
  ScenarioResultPayload,
  WorkbenchBootstrap,
  WorkbenchNavigationPayload
} from './types'


async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init)
  if (!response.ok) {
    throw new Error(`请求失败: ${response.status}`)
  }
  const payload = await response.json()
  if (!payload.success) {
    throw new Error(payload.error?.message || '请求失败')
  }
  return payload.data as T
}

export function fetchWorkbenchBootstrap(): Promise<WorkbenchBootstrap> {
  return request('/api/v2/workbench/bootstrap/')
}

export function fetchWorkbenchNavigation(): Promise<WorkbenchNavigationPayload> {
  return request('/api/v2/workbench/navigation/')
}

export function fetchScenarioDetail(scenarioId: string): Promise<ScenarioDetailPayload> {
  return request(`/api/v2/scenarios/${scenarioId}/`)
}

export function fetchScenarioResult(scenarioId: string): Promise<ScenarioResultPayload> {
  return request(`/api/v2/scenarios/${scenarioId}/result/`)
}

export function executeScenario(scenarioId: string): Promise<unknown> {
  return request(`/api/v2/scenarios/${scenarioId}/execute/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      trigger_source: 'manual'
    })
  })
}

export function retryFailedScenario(scenarioId: string): Promise<unknown> {
  return request(`/api/v2/scenarios/${scenarioId}/execute/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      trigger_source: 'retry_failed'
    })
  })
}
