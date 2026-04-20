<template>
  <div class="tree-group">
    <div
      v-for="project in projects"
      :key="project.project_code"
      class="tree-card"
    >
      <strong class="tree-project">{{ project.project_name }}</strong>
      <div
        v-for="module in project.modules"
        :key="`${project.project_code}-${module.module_code}`"
        class="tree-module"
      >
        <span class="tree-label">模块</span>
        <h3 class="tree-heading">{{ module.module_name }}</h3>
        <div
          v-for="submodule in module.submodules"
          :key="`${module.module_code}-${submodule.submodule_code}`"
          class="tree-submodule"
        >
          <span class="tree-label">子模块</span>
          <p class="tree-subtitle">{{ submodule.submodule_name }}</p>
          <button
            v-for="testcase in submodule.testcases"
            :key="testcase.scenario_id"
            :data-testid="`testcase-node-${testcase.scenario_id}`"
            class="tree-testcase"
            type="button"
            @click="$emit('selectTestcase', testcase.scenario_id)"
          >
            <span>{{ testcase.scenario_name }}</span>
            <small>{{ testcase.scenario_code }}</small>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { WorkbenchProjectNode } from '../services/types'

defineProps<{
  projects: WorkbenchProjectNode[]
}>()

defineEmits<{
  selectTestcase: [scenarioId: string]
}>()
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

.tree-testcase small {
  color: var(--color-muted);
}
</style>
