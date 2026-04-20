<template>
  <div class="detail-panel">
    <template v-if="detail">
      <div class="detail-card">
        <span class="detail-label">测试用例</span>
        <h3>{{ detail.scenario_name }}</h3>
        <p>{{ detail.scenario_code }}</p>
      </div>
      <div class="detail-card">
        <span class="detail-label">执行结果</span>
        <p>{{ result?.execution_status || 'not_started' }}</p>
        <p>{{ result?.latest_execution_id || '未执行' }}</p>
        <p>{{ result?.report_path || '暂无报告' }}</p>
      </div>
      <div class="button-row">
        <button data-testid="execute-testcase-button" type="button" class="primary-button" @click="$emit('execute')">
          执行测试
        </button>
        <button
          data-testid="retry-failed-testcase-button"
          type="button"
          class="secondary-button"
          :disabled="!result?.retry_available"
          @click="$emit('retry')"
        >
          失败重试
        </button>
      </div>
    </template>
    <div v-else class="detail-empty">
      请选择测试用例查看详情。
    </div>
  </div>
</template>

<script setup lang="ts">
import type { ScenarioDetailPayload, ScenarioResultPayload } from '../services/types'

defineProps<{
  detail: ScenarioDetailPayload | null
  result: ScenarioResultPayload | null
}>()

defineEmits<{
  execute: []
  retry: []
}>()
</script>

<style scoped>
.detail-panel {
  display: grid;
  gap: 12px;
}

.detail-card,
.detail-empty {
  padding: 16px;
  border: 1px solid var(--color-border);
  border-radius: 18px;
  background: var(--color-surface);
}

.detail-label {
  color: var(--color-muted);
  font-size: 0.74rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.detail-card h3,
.detail-card p {
  margin: 8px 0 0;
}

.button-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.primary-button,
.secondary-button {
  padding: 12px 18px;
  border: 1px solid var(--color-border);
  border-radius: 999px;
  cursor: pointer;
}

.primary-button {
  background: var(--color-accent);
  color: #fffefb;
  border-color: var(--color-accent);
}

.secondary-button {
  background: var(--color-soft);
  color: var(--color-ink);
}

.secondary-button:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}
</style>
