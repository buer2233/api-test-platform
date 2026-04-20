<template>
  <div class="list-panel">
    <article
      v-for="item in interfaces"
      :key="item.interface_id"
      class="interface-card"
    >
      <span class="interface-method">{{ item.http_method }}</span>
      <strong>{{ item.method_name }}</strong>
      <small>{{ item.path_template }}</small>
    </article>
  </div>
</template>

<script setup lang="ts">
import type { WorkbenchTestInterfaceSummary } from '../services/types'

defineProps<{
  interfaces: WorkbenchTestInterfaceSummary[]
}>()
</script>

<style scoped>
.list-panel {
  display: grid;
  gap: 12px;
}

.interface-card {
  display: grid;
  gap: 6px;
  padding: 16px;
  border: 1px solid var(--color-border);
  border-radius: 18px;
  background: rgba(255, 79, 0, 0.05);
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
</style>
