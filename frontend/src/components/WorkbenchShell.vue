<template>
  <main class="workbench-page">
    <header class="hero">
      <span class="eyebrow">API TEST WORKBENCH</span>
      <h1 class="hero-title">{{ title }}</h1>
      <p class="hero-copy">
        基于 DESIGN.md 的 Vue3 三段式工作台壳层，后续将在这里接入项目、模块、子模块、测试用例、测试接口和执行结果。
      </p>
    </header>
    <section class="workbench-shell">
      <aside class="panel" data-testid="left-tree-panel">
        <span class="panel-label">项目导航</span>
        <h2 class="panel-title">项目 / 模块 / 子模块</h2>
        <slot name="left">
          <p class="panel-copy">左侧树区承接项目、模块、子模块、测试用例和测试接口五级导航。</p>
        </slot>
      </aside>
      <section class="panel" data-testid="middle-list-panel">
        <span class="panel-label">主工作列</span>
        <h2 class="panel-title">当前层级对象</h2>
        <slot name="middle">
          <p class="panel-copy">中间列用于展示当前层级对象列表与抓包、生成、执行等主动作。</p>
        </slot>
      </section>
      <section class="panel" data-testid="right-detail-panel">
        <span class="panel-label">详情与执行</span>
        <h2 class="panel-title">详情 / 报告 / 重试</h2>
        <slot name="right">
          <p class="panel-copy">右侧详情区承接测试用例详情、执行结果、报告入口和失败重试。</p>
        </slot>
      </section>
    </section>
  </main>
</template>

<script setup lang="ts">
defineProps<{
  title: string
}>()
</script>

<style scoped>
.workbench-page {
  min-height: 100vh;
  padding: 32px;
  background:
    radial-gradient(circle at top right, rgba(255, 79, 0, 0.12), transparent 20%),
    radial-gradient(circle at bottom left, rgba(197, 192, 177, 0.24), transparent 30%),
    var(--color-page);
  color: var(--color-ink);
}

.hero {
  max-width: 1240px;
  margin: 0 auto 24px;
  padding: 28px;
  border: 1px solid var(--color-border);
  border-radius: 20px;
  background: rgba(255, 254, 251, 0.92);
}

.eyebrow {
  display: inline-flex;
  align-items: center;
  padding: 8px 12px;
  border: 1px solid var(--color-border);
  border-radius: 999px;
  color: var(--color-accent);
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.12em;
}

.hero-title {
  margin: 18px 0 12px;
  font-family: var(--font-display);
  font-size: clamp(2.75rem, 5vw, 4.5rem);
  line-height: 0.92;
  font-weight: 500;
}

.hero-copy {
  max-width: 760px;
  margin: 0;
  color: var(--color-copy);
  line-height: 1.7;
}

.workbench-shell {
  display: grid;
  grid-template-columns: 280px minmax(320px, 1fr) minmax(360px, 1.08fr);
  gap: 20px;
  max-width: 1240px;
  margin: 0 auto;
}

.panel {
  min-height: 340px;
  padding: 24px;
  border: 1px solid var(--color-border);
  border-radius: 20px;
  background: rgba(255, 254, 251, 0.96);
}

.panel-label {
  display: inline-flex;
  align-items: center;
  margin-bottom: 12px;
  color: var(--color-muted);
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.panel-title {
  margin: 0 0 10px;
  font-size: 1.5rem;
  font-weight: 600;
}

.panel-copy {
  margin: 0;
  color: var(--color-copy);
  line-height: 1.7;
}

@media (max-width: 1080px) {
  .workbench-page {
    padding: 20px;
  }

  .workbench-shell {
    grid-template-columns: 1fr;
  }
}
</style>
