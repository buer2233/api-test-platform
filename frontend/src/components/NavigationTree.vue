<template>
  <div class="tree-group">
    <div
      v-for="project in projects"
      :key="project.project_code"
      class="tree-card"
    >
      <button
        :data-testid="`project-node-${project.project_code}`"
        class="tree-project-button"
        type="button"
        @click="$emit('selectProject', project.project_code)"
      >
        {{ project.project_name }}
      </button>
      <div
        v-if="project.project_code === selectedProjectCode"
        class="tree-module"
      >
        <button
          v-for="module in project.modules"
          :key="`${project.project_code}-${module.module_code}`"
          :data-testid="`module-node-${module.module_code}`"
          class="tree-section-button"
          type="button"
          @click="$emit('selectModule', project.project_code, module.module_code)"
        >
          <span class="tree-label">模块</span>
          <strong class="tree-heading">{{ module.module_name }}</strong>
        </button>
        <div
          v-if="selectedModule && selectedModule.module_code"
          class="tree-submodule"
        >
          <button
            v-for="submodule in selectedModule.submodules"
            :key="`${selectedModule.module_code}-${submodule.submodule_code}`"
            :data-testid="`submodule-node-${submodule.submodule_code}`"
            class="tree-section-button"
            type="button"
            @click="$emit('selectSubmodule', selectedProjectCode, selectedModule.module_code, submodule.submodule_code)"
          >
            <span class="tree-label">子模块</span>
            <strong class="tree-heading">{{ submodule.submodule_name }}</strong>
          </button>
        </div>
      </div>
      <div
        v-if="project.project_code === selectedProjectCode && selectedSubmodule"
        class="tree-leaf-actions"
      >
        <button
          data-testid="tree-switch-testcases"
          class="tree-chip"
          type="button"
          :class="{ active: currentView === 'testcases' }"
          @click="$emit('switchView', 'testcases')"
        >
          测试用例
        </button>
        <button
          data-testid="tree-switch-interfaces"
          class="tree-chip"
          type="button"
          :class="{ active: currentView === 'interfaces' }"
          @click="$emit('switchView', 'interfaces')"
        >
          测试接口
        </button>
      </div>
      <div
        v-if="project.project_code === selectedProjectCode && selectedSubmodule && currentView === 'testcases'"
        class="tree-submodule"
      >
        <button
          v-for="testcase in selectedSubmodule.testcases"
          :key="testcase.scenario_id"
          :data-testid="`testcase-node-${testcase.scenario_id}`"
          class="tree-testcase"
          :class="{ active: testcase.scenario_id === selectedScenarioId }"
          type="button"
          @click="$emit('selectTestcase', testcase.scenario_id)"
        >
          <span>{{ testcase.scenario_name }}</span>
          <small>{{ testcase.scenario_code }}</small>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

import type { WorkbenchMiddleView, WorkbenchProjectNode, WorkbenchSubmoduleNode } from '../services/types'

const props = defineProps<{
  projects: WorkbenchProjectNode[]
  selectedProjectCode: string
  selectedModuleCode: string
  selectedSubmoduleCode: string
  selectedScenarioId: string
  currentView: WorkbenchMiddleView
}>()

defineEmits<{
  selectProject: [projectCode: string]
  selectModule: [projectCode: string, moduleCode: string]
  selectSubmodule: [projectCode: string, moduleCode: string, submoduleCode: string]
  selectTestcase: [scenarioId: string]
  switchView: [view: 'testcases' | 'interfaces']
}>()

const selectedProject = computed(() =>
  props.projects.find((item) => item.project_code === props.selectedProjectCode) ?? null
)

const selectedModule = computed(() =>
  selectedProject.value?.modules.find((item) => item.module_code === props.selectedModuleCode) ?? null
)

const selectedSubmodule = computed<WorkbenchSubmoduleNode | null>(() =>
  selectedModule.value?.submodules.find((item) => item.submodule_code === props.selectedSubmoduleCode) ?? null
)
</script>

<style scoped>
.tree-group {
  display: grid;
  gap: 14px;
}

.tree-card,
.tree-module,
.tree-submodule {
  display: grid;
  gap: 8px;
}

.tree-card {
  padding: 16px;
  border: 1px solid var(--color-border);
  border-radius: 18px;
  background: var(--color-surface);
}

.tree-project,
.tree-heading,
.tree-subtitle {
  margin: 0;
}

.tree-project-button,
.tree-section-button {
  width: 100%;
  display: grid;
  gap: 6px;
  padding: 14px;
  border: 1px solid var(--color-border);
  border-radius: 16px;
  background: rgba(255, 79, 0, 0.05);
  color: var(--color-ink);
  text-align: left;
  cursor: pointer;
}

.tree-label {
  color: var(--color-muted);
  font-size: 0.74rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.tree-testcase {
  display: grid;
  gap: 4px;
  padding: 12px 14px;
  border: 1px solid var(--color-border);
  border-radius: 14px;
  background: rgba(255, 79, 0, 0.04);
  color: var(--color-ink);
  text-align: left;
  cursor: pointer;
}

.tree-testcase.active,
.tree-chip.active {
  border-color: var(--color-accent);
  background: rgba(255, 79, 0, 0.12);
}

.tree-chip {
  padding: 10px 14px;
  border: 1px solid var(--color-border);
  border-radius: 999px;
  background: var(--color-soft);
  color: var(--color-ink);
  cursor: pointer;
}

.tree-leaf-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tree-testcase small {
  color: var(--color-muted);
}
</style>
