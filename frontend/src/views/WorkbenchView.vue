<template>
  <WorkbenchShell :title="bootstrap?.page_title || '抓包与接口自动化工作台'">
    <template #left>
      <NavigationTree :projects="navigation.projects" @select-testcase="handleSelectTestcase" />
    </template>
    <template #middle>
      <WorkbenchListPanel :interfaces="selectedInterfaces" />
    </template>
    <template #right>
      <WorkbenchDetailPanel :detail="selectedDetail" :result="selectedResult" @execute="handleExecute" @retry="handleRetry" />
    </template>
  </WorkbenchShell>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import WorkbenchDetailPanel from '../components/WorkbenchDetailPanel.vue'
import WorkbenchListPanel from '../components/WorkbenchListPanel.vue'
import WorkbenchShell from '../components/WorkbenchShell.vue'
import NavigationTree from '../components/NavigationTree.vue'
import {
  executeScenario,
  fetchScenarioDetail,
  fetchScenarioResult,
  fetchWorkbenchBootstrap,
  fetchWorkbenchNavigation,
  retryFailedScenario
} from '../services/api'
import type {
  ScenarioDetailPayload,
  ScenarioResultPayload,
  WorkbenchBootstrap,
  WorkbenchNavigationPayload,
  WorkbenchTestInterfaceSummary
} from '../services/types'

const bootstrap = ref<WorkbenchBootstrap | null>(null)
const navigation = ref<WorkbenchNavigationPayload>({
  projects: []
})
const selectedScenarioId = ref('')
const selectedDetail = ref<ScenarioDetailPayload | null>(null)
const selectedResult = ref<ScenarioResultPayload | null>(null)

const selectedInterfaces = computed<WorkbenchTestInterfaceSummary[]>(() => {
  for (const project of navigation.value.projects) {
    for (const module of project.modules) {
      for (const submodule of module.submodules) {
        if (submodule.testcases.some((item) => item.scenario_id === selectedScenarioId.value)) {
          return submodule.test_interfaces
        }
      }
    }
  }
  const firstProject = navigation.value.projects[0]
  const firstModule = firstProject?.modules[0]
  const firstSubmodule = firstModule?.submodules[0]
  return firstSubmodule?.test_interfaces ?? []
})

async function loadScenario(scenarioId: string): Promise<void> {
  selectedScenarioId.value = scenarioId
  selectedDetail.value = await fetchScenarioDetail(scenarioId)
  selectedResult.value = await fetchScenarioResult(scenarioId)
}

async function handleSelectTestcase(scenarioId: string): Promise<void> {
  await loadScenario(scenarioId)
}

async function handleExecute(): Promise<void> {
  if (!selectedScenarioId.value) {
    return
  }
  await executeScenario(selectedScenarioId.value)
  selectedResult.value = await fetchScenarioResult(selectedScenarioId.value)
}

async function handleRetry(): Promise<void> {
  if (!selectedScenarioId.value) {
    return
  }
  await retryFailedScenario(selectedScenarioId.value)
  selectedResult.value = await fetchScenarioResult(selectedScenarioId.value)
}

onMounted(async () => {
  bootstrap.value = await fetchWorkbenchBootstrap()
  navigation.value = await fetchWorkbenchNavigation()
  const firstScenarioId = navigation.value.projects[0]?.modules[0]?.submodules[0]?.testcases[0]?.scenario_id
  if (firstScenarioId) {
    await loadScenario(firstScenarioId)
  }
})
</script>
