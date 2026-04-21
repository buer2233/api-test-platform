<template>
  <div class="list-panel">
    <div class="list-header">
      <h3 data-testid="middle-panel-title" class="list-title">{{ title }}</h3>
      <div v-if="enableViewSwitch" class="list-switch">
        <button
          data-testid="switch-view-testcases"
          class="switch-button"
          :class="{ active: currentView === 'testcases' }"
          type="button"
          @click="$emit('switchView', 'testcases')"
        >
          测试用例
        </button>
        <button
          data-testid="switch-view-interfaces"
          class="switch-button"
          :class="{ active: currentView === 'interfaces' }"
          type="button"
          @click="$emit('switchView', 'interfaces')"
        >
          测试接口
        </button>
      </div>
    </div>
    <button
      v-for="item in pagedItems"
      :key="item.id"
      :data-testid="`middle-item-${currentView === 'interfaces' ? 'interface' : currentView}-${item.id}`"
      class="interface-card"
      :class="{ active: item.id === selectedItemId }"
      type="button"
      @click="$emit('selectItem', item.id)"
    >
      <span v-if="item.badge" class="interface-method">{{ item.badge }}</span>
      <strong>{{ item.title }}</strong>
      <small>{{ item.subtitle }}</small>
    </button>
    <div v-if="totalPages > 1" class="pagination">
      <button
        data-testid="pagination-prev"
        class="switch-button"
        type="button"
        :disabled="currentPage <= 1"
        @click="$emit('previousPage')"
      >
        上一页
      </button>
      <span data-testid="pagination-indicator" class="page-indicator">{{ currentPage }} / {{ totalPages }}</span>
      <button
        data-testid="pagination-next"
        class="switch-button"
        type="button"
        :disabled="currentPage >= totalPages"
        @click="$emit('nextPage')"
      >
        下一页
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { WorkbenchMiddleView } from '../services/types'

defineProps<{
  title: string
  currentView: WorkbenchMiddleView
  items: Array<{
    id: string
    title: string
    subtitle: string
    badge?: string
  }>
  pagedItems: Array<{
    id: string
    title: string
    subtitle: string
    badge?: string
  }>
  currentPage: number
  totalPages: number
  selectedItemId: string
  enableViewSwitch: boolean
}>()

defineEmits<{
  selectItem: [itemId: string]
  switchView: [view: 'testcases' | 'interfaces']
  previousPage: []
  nextPage: []
}>()
</script>

<style scoped>
.list-panel {
  display: grid;
  gap: 12px;
}

.list-header {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 12px;
}

.list-title {
  margin: 0;
  font-size: 1.2rem;
}

.list-switch,
.pagination {
  display: flex;
  align-items: center;
  gap: 8px;
}

.interface-card {
  display: grid;
  gap: 6px;
  padding: 16px;
  border: 1px solid var(--color-border);
  border-radius: 18px;
  background: rgba(255, 79, 0, 0.05);
  color: var(--color-ink);
  text-align: left;
  cursor: pointer;
}

.interface-method {
  color: var(--color-accent);
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.1em;
}

.interface-card small {
  color: var(--color-muted);
}

.switch-button {
  padding: 10px 14px;
  border: 1px solid var(--color-border);
  border-radius: 999px;
  background: var(--color-soft);
  color: var(--color-ink);
  cursor: pointer;
}

.switch-button.active,
.interface-card.active {
  border-color: var(--color-accent);
  background: rgba(255, 79, 0, 0.12);
}

.switch-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-indicator {
  color: var(--color-muted);
  font-size: 0.9rem;
}
</style>
