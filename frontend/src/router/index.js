import { createRouter, createWebHistory } from 'vue-router';
import MainLayout from '../layouts/MainLayout.vue';
import Dashboard from '../views/Dashboard.vue';
import TemplateLib from '../views/TemplateLib.vue';
import FilesPage from "../views/FilesPage.vue";
import Login from "../views/Login.vue"; // ✅ 确保引入了 Login 组件

const routes = [
    // 1. 登录页 (独立路由，不使用 MainLayout)
    {
        path: '/login',
        name: 'Login',
        component: Login,
        meta: { title: '用户登录' }
    },

    // 2. 主应用区域 (包含侧边栏和顶栏)
    {
        path: '/',
        component: MainLayout,
        redirect: '/dashboard', // 访问根路径默认跳到工作台
        // 只有在这些子路由下，MainLayout 才会显示
        children: [
            {
                path: 'dashboard',
                name: 'Dashboard',
                component: Dashboard,
                meta: { title: 'AI 智能工作台', requiresAuth: true }
            },
            {
                path: 'filespage',
                name: 'files',
                component: FilesPage,
                meta: { title: '已上传表格', requiresAuth: true }
            },
            {
                path: 'templates',
                name: 'Templates',
                component: TemplateLib,
                meta: { title: '公式模板库', requiresAuth: true }
            }
        ]
    }
];

const router = createRouter({
    history: createWebHistory(),
    routes
});

// --- 🛡️ 路由守卫 (可选但推荐) ---
// 作用：如果用户没登录，强制跳转到登录页；如果已登录，禁止回登录页
router.beforeEach((to, from, next) => {
    const isAuthenticated = localStorage.getItem('isLoggedIn'); // 检查本地是否有登录标记

    if (to.path === '/login' && isAuthenticated) {
        // 如果已登录还想去登录页，踢回首页
        next('/');
    } else if (to.matched.some(record => record.meta.requiresAuth) && !isAuthenticated) {
        // 如果要去需要权限的页面但没登录，踢去登录页
        next('/login');
    } else {
        // 正常放行
        next();
    }
});

export default router;