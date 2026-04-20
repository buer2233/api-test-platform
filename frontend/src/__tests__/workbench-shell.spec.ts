import { mount } from '@vue/test-utils'

import WorkbenchShell from '../components/WorkbenchShell.vue'

describe('WorkbenchShell', () => {
  it('渲染三段式工作台壳层并显示设计系统标题', () => {
    const wrapper = mount(WorkbenchShell, {
      props: {
        title: '抓包与接口自动化工作台'
      }
    })

    expect(wrapper.text()).toContain('抓包与接口自动化工作台')
    expect(wrapper.find('[data-testid="left-tree-panel"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="middle-list-panel"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="right-detail-panel"]').exists()).toBe(true)
  })
})
