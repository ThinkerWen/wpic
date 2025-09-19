import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/store'

// 路由组件懒加载
const Login = () => import('@/views/Login.vue')
const Dashboard = () => import('@/views/Dashboard.vue')
const Upload = () => import('@/views/Upload.vue')
const Gallery = () => import('@/views/Gallery.vue')
const Settings = () => import('@/views/Settings.vue')
const NotFound = () => import('@/views/NotFound.vue')

const routes = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: {
      requiresAuth: false,
      title: '登录'
    }
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: Dashboard,
    meta: {
      requiresAuth: true,
      title: '仪表板'
    }
  },
  {
    path: '/upload',
    name: 'Upload',
    component: Upload,
    meta: {
      requiresAuth: true,
      title: '上传图片'
    }
  },
  {
    path: '/gallery',
    name: 'Gallery',
    component: Gallery,
    meta: {
      requiresAuth: true,
      title: '图片库'
    }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: Settings,
    meta: {
      requiresAuth: true,
      requiresAdmin: true,
      title: '系统设置'
    }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: NotFound,
    meta: {
      title: '页面未找到'
    }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  }
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  
  // 更新页面标题
  if (to.meta.title) {
    document.title = `${to.meta.title} - ${import.meta.env.VITE_APP_TITLE}`
  }

  // 如果已经登录且访问登录页，重定向到首页
  if (to.name === 'Login' && authStore.isAuthenticated) {
    next('/dashboard')
    return
  }

  // 检查是否需要认证
  if (to.meta.requiresAuth) {
    if (!authStore.isAuthenticated) {
      // 如果没有 token，跳转到登录页
      next({
        name: 'Login',
        query: { redirect: to.fullPath }
      })
      return
    }

    // 如果有 token 但没有用户信息，尝试获取用户信息
    if (!authStore.user) {
      try {
        await authStore.getCurrentUser()
      } catch (error) {
        // 获取用户信息失败，跳转到登录页
        next({
          name: 'Login',
          query: { redirect: to.fullPath }
        })
        return
      }
    }

    // 检查是否需要管理员权限
    if (to.meta.requiresAdmin && !authStore.isAdmin) {
      // 没有管理员权限，跳转到首页
      next('/dashboard')
      return
    }
  }

  next()
})

export default router