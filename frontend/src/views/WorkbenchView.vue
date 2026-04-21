<template>
  <WorkbenchShell :title="bootstrap?.page_title || '抓包与接口自动化工作台'">
    <template #left>
      <NavigationTree
        :projects="navigation.projects"
        :selected-project-code="selectedProjectCode"
        :selected-module-code="selectedModuleCode"
        :selected-submodule-code="selectedSubmoduleCode"
        :selected-scenario-id="selectedScenarioId"
        :current-view="currentView"
        @select-project="handleSelectProject"
        @select-module="handleSelectModule"
        @select-submodule="handleSelectSubmodule"
        @select-testcase="handleSelectTestcase"
        @switch-view="handleSwitchView"
      />
    </template>
    <template #middle>
      <WorkbenchListPanel
        :title="middlePanelTitle"
        :current-view="currentView"
        :items="middleItems"
        :paged-items="pagedMiddleItems"
        :current-page="currentPage"
        :total-pages="totalPages"
        :selected-item-id="selectedItemId"
        :enable-view-switch="canSwitchViews"
        @select-item="handleSelectMiddleItem"
        @switch-view="handleSwitchView"
        @previous-page="goPreviousPage"
        @next-page="goNextPage"
      />
    </template>
    <template #right>
      <WorkbenchDetailPanel
        :detail="selectedDetail"
        :result="selectedResult"
        :interface-detail="selectedInterfaceDetail"
        @execute="handleExecute"
        @retry="handleRetry"
      />
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
  fetchTestInterfaceDetail,
  fetchWorkbenchBootstrap,
  fetchWorkbenchNavigation,
  retryFailedScenario
} from '../services/api'
import type {
  ScenarioDetailPayload,
  ScenarioResultPayload,
  WorkbenchBootstrap,
  WorkbenchMiddleView,
  WorkbenchNavigationPayload,
  WorkbenchTestInterfaceDetail
} from '../services/types'

const bootstrap = ref<WorkbenchBootstrap | null>(null)
const navigation = ref<WorkbenchNavigationPayload>({
  projects: []
})
const selectedProjectCode = ref('')
const selectedModuleCode = ref('')
const selectedSubmoduleCode = ref('')
const selectedScenarioId = ref('')
const selectedInterfaceId = ref('')
const selectedDetail = ref<ScenarioDetailPayload | null>(null)
const selectedResult = ref<ScenarioResultPayload | null>(null)
const selectedInterfaceDetail = ref<WorkbenchTestInterfaceDetail | null>(null)
const currentView = ref<WorkbenchMiddleView>('modules')
const currentPage = ref(1)

const selectedProject = computed(() =>
  navigation.value.projects.find((item) => item.project_code === selectedProjectCode.value) ?? null
)

const selectedModule = computed(() =>
  selectedProject.value?.modules.find((item) => item.module_code === selectedModuleCode.value) ?? null
)

const selectedSubmodule = computed(() =>
  selectedModule.value?.submodules.find((item) => item.submodule_code === selectedSubmoduleCode.value) ?? null
)

const canSwitchViews = computed(() => Boolean(selectedSubmodule.value))

const pageSize = computed(() => {
  if (currentView.value === 'interfaces') {
    return 10
  }
  if (currentView.value === 'testcases') {
    return 8
  }
  return 12
})

const middleItems = computed(() => {
  if (currentView.value === 'modules') {
    return selectedProject.value?.modules.map((item) => ({
      id: item.module_code,
      title: item.module_name,
      subtitle: item.module_code
    })) ?? []
  }
  if (currentView.value === 'submodules') {
    return selectedModule.value?.submodules.map((item) => ({
      id: item.submodule_code,
      title: item.submodule_name,
      subtitle: item.submodule_code
    })) ?? []
  }
  if (currentView.value === 'testcases') {
    return selectedSubmodule.value?.testcases.map((item) => ({
      id: item.scenario_id,
      title: item.scenario_name,
      subtitle: item.scenario_code,
      badge: item.execution_status
    })) ?? []
  }
  return selectedSubmodule.value?.test_interfaces.map((item) => ({
    id: item.interface_id,
    title: item.method_name,
    subtitle: item.path_template,
    badge: item.http_method
  })) ?? []
})

const totalPages = computed(() => Math.max(1, Math.ceil(middleItems.value.length / pageSize.value)))

const pagedMiddleItems = computed(() => {
  const startIndex = (currentPage.value - 1) * pageSize.value
  return middleItems.value.slice(startIndex, startIndex + pageSize.value)
})

const middlePanelTitle = computed(() => {
  switch (currentView.value) {
    case 'modules':
      return '模块'
    case 'submodules':
      return '子模块'
    case 'testcases':
      return '测试用例'
    case 'interfaces':
      return '测试接口'
  }
})

const selectedItemId = computed(() => {
  if (currentView.value === 'testcases') {
    return selectedScenarioId.value
  }
  if (currentView.value === 'interfaces') {
    return selectedInterfaceId.value
  }
  if (currentView.value === 'submodules') {
    return selectedSubmoduleCode.value
  }
  return selectedModuleCode.value
})

async function loadScenario(scenarioId: string): Promise<void> {
  selectedScenarioId.value = scenarioId
  selectedInterfaceId.value = ''
  selectedInterfaceDetail.value = null
  selectedDetail.value = await fetchScenarioDetail(scenarioId)
  selectedResult.value = await fetchScenarioResult(scenarioId)
}

async function loadInterfaceDetail(interfaceId: string): Promise<void> {
  selectedInterfaceId.value = interfaceId
  selectedScenarioId.value = ''
  selectedDetail.value = null
  selectedResult.value = null
  selectedInterfaceDetail.value = await fetchTestInterfaceDetail(interfaceId)
}

function resetPaging(): void {
  currentPage.value = 1
}

function clearDetailState(): void {
  selectedScenarioId.value = ''
  selectedInterfaceId.value = ''
  selectedDetail.value = null
  selectedResult.value = null
  selectedInterfaceDetail.value = null
}

function handleSelectProject(projectCode: string): void {
  selectedProjectCode.value = projectCode
  selectedModuleCode.value = ''
  selectedSubmoduleCode.value = ''
  currentView.value = 'modules'
  resetPaging()
  clearDetailState()
}

function handleSelectModule(projectCode: string, moduleCode: string): void {
  selectedProjectCode.value = projectCode
  selectedModuleCode.value = moduleCode
  selectedSubmoduleCode.value = ''
  currentView.value = 'submodules'
  resetPaging()
  clearDetailState()
}

async function handleSelectSubmodule(projectCode: string, moduleCode: string, submoduleCode: string): Promise<void> {
  selectedProjectCode.value = projectCode
  selectedModuleCode.value = moduleCode
  selectedSubmoduleCode.value = submoduleCode
  currentView.value = 'testcases'
  resetPaging()
  clearDetailState()
  const firstScenarioId = selectedSubmodule.value?.testcases[0]?.scenario_id
  if (firstScenarioId) {
    await loadScenario(firstScenarioId)
  }
}

async function handleSelectTestcase(scenarioId: string): Promise<void> {
  currentView.value = 'testcases'
  await loadScenario(scenarioId)
}

async function handleSelectMiddleItem(itemId: string): Promise<void> {
  if (currentView.value === 'modules') {
    handleSelectModule(selectedProjectCode.value, itemId)
    return
  }
  if (currentView.value === 'submodules') {
    await handleSelectSubmodule(selectedProjectCode.value, selectedModuleCode.value, itemId)
    return
  }
  if (currentView.value === 'testcases') {
    await loadScenario(itemId)
    return
  }
  await loadInterfaceDetail(itemId)
}

async function handleSwitchView(view: 'testcases' | 'interfaces'): Promise<void> {
  currentView.value = view
  resetPaging()
  if (view === 'testcases') {
    selectedInterfaceId.value = ''
    selectedInterfaceDetail.value = null
    const firstScenarioId = selectedSubmodule.value?.testcases[0]?.scenario_id
    if (firstScenarioId) {
      await loadScenario(firstScenarioId)
    }
    return
  }
  clearDetailState()
}

function goPreviousPage(): void {
  currentPage.value = Math.max(1, currentPage.value - 1)
}

function goNextPage(): void {
  currentPage.value = Math.min(totalPages.value, currentPage.value + 1)
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
  const firstProject = navigation.value.projects[0]
  if (!firstProject) {
    return
  }
  selectedProjectCode.value = firstProject.project_code
  const firstModule = firstProject.modules[0]
  if (!firstModule) {
    currentView.value = 'modules'
    return
  }
  selectedModuleCode.value = firstModule.module_code
  const firstSubmodule = firstModule.submodules[0]
  if (!firstSubmodule) {
    currentView.value = 'submodules'
    return
  }
  selectedSubmoduleCode.value = firstSubmodule.submodule_code
  currentView.value = 'testcases'
  const firstScenarioId = firstSubmodule.testcases[0]?.scenario_id
  if (firstScenarioId) {
    await loadScenario(firstScenarioId)
  }
})
</script>
