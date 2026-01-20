<template>
  <a-layout style="min-height: 100vh">
    <a-layout-sider v-model:collapsed="collapsed" collapsible theme="dark" width="240">
      <div class="logo-area">
        <robot-outlined class="logo-icon" />
        <span v-if="!collapsed" class="logo-text">Excel 智动化</span>
      </div>

      <a-menu v-model:selectedKeys="selectedKeys" theme="dark" mode="inline">

        <a-menu-item key="dashboard" @click="handleMenuClick('/dashboard')">
          <thunderbolt-outlined />
          <span>AI 工作台</span>
        </a-menu-item>

        <a-menu-item key="files" @click="handleMenuClick('/filespage')">
          <table-outlined />
          <span>已上传表格</span>
        </a-menu-item>

        <a-menu-item key="templates" @click="handleMenuClick('/templates')">
          <book-outlined />
          <span>公式模板库</span>
        </a-menu-item>
      </a-menu>
    </a-layout-sider>

    <a-layout>
      <a-layout-header style="background: #fff; padding: 0 24px; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 1px 4px rgba(0,21,41,0.08);">
        <div class="header-title">{{ currentTitle }}</div>

        <div class="user-info">
          <a-dropdown placement="bottomRight">
            <div class="user-link">
              <a-avatar style="background-color: #1890ff" size="small">U</a-avatar>
              <span style="margin-left: 8px; font-weight: 500;">员工A</span>
              <down-outlined style="margin-left: 5px; font-size: 12px; color: #666;" />
            </div>

            <template #overlay>
              <a-menu>
                <a-menu-item key="profile">
                  <user-outlined /> 个人资料
                </a-menu-item>
                <a-menu-divider />
                <a-menu-item key="logout" @click="handleLogout">
                  <logout-outlined /> 退出登录
                </a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>
        </div>
      </a-layout-header>

      <a-layout-content style="margin: 24px 16px; padding: 24px; background: #fff; min-height: 280px; border-radius: 8px;">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </a-layout-content>

      <a-layout-footer style="text-align: center; color: #999;">
        Excel Automation System ©2026 Internal Use Only
      </a-layout-footer>
    </a-layout>
  </a-layout>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { message } from 'ant-design-vue';
import {
  RobotOutlined,
  ThunderboltOutlined,
  BookOutlined,
  TableOutlined,
  DownOutlined,
  UserOutlined,
  LogoutOutlined
} from '@ant-design/icons-vue';

const collapsed = ref(false);
const route = useRoute();
const router = useRouter();

// --- 菜单高亮逻辑 (修复版) ---

const selectedKeys = ref([]);

// 🟢 核心修复：根据路径映射到菜单 Key
// 这样无论你的路由 name 叫 'Dashboard' 还是 'dashboard' 都不影响
const getMenuKeyFromPath = (path) => {
  if (path.startsWith('/filespage')) return 'files';    // 对应 key="files"
  if (path.startsWith('/templates')) return 'templates';// 对应 key="templates"
  // 默认认为是工作台 (包含 /dashboard 或 根路径 / )
  return 'dashboard';                                   // 对应 key="dashboard"
};

// 监听路由路径变化，自动更新高亮
watch(
    () => route.path,
    (newPath) => {
      const key = getMenuKeyFromPath(newPath);
      selectedKeys.value = [key];
    },
    { immediate: true } // 🟢 重要：初始化时立即执行一次，确保刷新后高亮正确
);

// --- 统一跳转处理 ---
const handleMenuClick = (path) => {
  router.push(path);
};

// --- 标题逻辑 ---
// 更加稳健的标题获取：如果没有 meta.title，根据路径判断
const currentTitle = computed(() => {
  if (route.meta?.title) return route.meta.title;

  // 兜底逻辑
  const path = route.path;
  if (path.includes('/filespage')) return '已上传表格';
  if (path.includes('/templates')) return '公式模板库';
  return 'AI 工作台';
});

// --- 用户逻辑 ---
const handleLogout = () => {
  // ✅ 新增：清除登录状态
  localStorage.removeItem('isLoggedIn');

  message.success('已安全退出');
  router.push('/login'); // 跳转回登录页
};
</script>

<style scoped>
.logo-area {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #002140;
  color: white;
  overflow: hidden;
  transition: all 0.3s;
}
.logo-icon { font-size: 24px; color: #1890ff; }
.logo-text { margin-left: 10px; font-size: 18px; font-weight: bold; white-space: nowrap; }

/* 顶部标题样式优化 */
.header-title {
  font-size: 22px;   /* 增大字体 */
  font-weight: 700;  /* 加粗 */
  color: #262626;
  letter-spacing: 0.5px;
}

/* 用户区域交互样式 */
.user-link {
  display: flex;
  align-items: center;
  cursor: pointer;
  padding: 4px 12px;
  border-radius: 4px;
  transition: all 0.3s;
}
.user-link:hover {
  background: rgba(0, 0, 0, 0.025);
}

/* 页面切换动画 */
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>