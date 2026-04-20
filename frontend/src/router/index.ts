import { createRouter, createWebHistory } from 'vue-router'

import WorkbenchView from '../views/WorkbenchView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/ui/v3/workbench/'
    },
    {
      path: '/ui/v2/workbench/',
      redirect: '/ui/v3/workbench/'
    },
    {
      path: '/ui/v3/workbench/',
      component: WorkbenchView
    }
  ]
})

export default router
