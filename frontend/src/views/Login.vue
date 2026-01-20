<template>
  <div class="login-container">

    <div class="left-section">
      <div class="grid-background"></div>

      <div class="fade-overlay"></div>

      <div class="brand-content">
        <div class="logo-wrapper">
          <robot-outlined class="brand-icon" />
        </div>
        <h1 class="brand-title">Excel 智动化</h1>

      </div>
    </div>

    <div class="right-section">
      <div class="login-box">
        <div class="form-header">
          <h2>欢迎登录</h2>
          <span class="sub-text">请输入您的账号密码</span>
        </div>

        <a-form
            :model="formState"
            name="basic"
            autocomplete="off"
            @finish="handleLogin"
            layout="vertical"
        >
          <a-form-item
              name="username"
              :rules="[{ required: true, message: '请输入用户名' }]"
          >
            <a-input
                v-model:value="formState.username"
                placeholder="用户名"
                size="large"
                class="custom-input"
            >
              <template #prefix>
                <user-outlined style="color: #1890ff" />
              </template>
            </a-input>
          </a-form-item>

          <a-form-item
              name="password"
              :rules="[{ required: true, message: '请输入密码' }]"
          >
            <a-input-password
                v-model:value="formState.password"
                placeholder="密码"
                size="large"
                class="custom-input"
            >
              <template #prefix>
                <lock-outlined style="color: #1890ff" />
              </template>
            </a-input-password>
          </a-form-item>

          <div class="form-options">
            <a-checkbox v-model:checked="formState.remember">记住我</a-checkbox>
            <a class="forgot-password">忘记密码？</a>
          </div>

          <a-form-item>
            <a-button
                type="primary"
                html-type="submit"
                block
                size="large"
                :loading="loading"
                class="login-btn"
            >
              立即登录
            </a-button>
          </a-form-item>
        </a-form>
      </div>

      <div class="copyright">
        Excel Automation System ©2026 Internal Use Only
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue';
import { useRouter } from 'vue-router';
import { message } from 'ant-design-vue';
import { UserOutlined, LockOutlined, RobotOutlined } from '@ant-design/icons-vue';

const router = useRouter();
const loading = ref(false);

const formState = reactive({
  username: '',
  password: '',
  remember: true,
});

// ... 在 handleLogin 函数内部 ...
const handleLogin = (values) => {
  loading.value = true;

  setTimeout(() => {
    loading.value = false;
    // ✅ 新增：设置登录状态
    localStorage.setItem('isLoggedIn', 'true');

    message.success('登录成功，正在进入工作台...');
    router.push('/dashboard');
  }, 1000);
};
</script>

<style scoped>
/* 全屏容器 */
.login-container {
  display: flex;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
}

/* ================= 左侧设计 ================= */
.left-section {
  position: relative;
  flex: 0 0 60%; /* 占据左侧 60% */
  background-color: #f8fbff; /* 极浅的底色 */
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  overflow: hidden;
}

/* 核心：CSS绘制 Excel 网格 */
.grid-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  /* 修改说明：
     1. 颜色改为 rgba(24, 144, 255, 0.15) -> 加深了颜色，确保肉眼可见
     2. 宽度改为 2px -> 这里的 '2px' 控制线条粗细，如果觉得还不够粗，可以改成 3px 或 4px
  */
  background-image:
      linear-gradient(rgba(24, 144, 255, 0.15) 2px, transparent 4px), /* 横线 */
      linear-gradient(90deg, rgba(24, 144, 255, 0.15) 4px, transparent 4px); /* 竖线 */

  background-size: 80px 40px; /* 单元格大小 */
  z-index: 1;
}

/* 核心：右侧边缘的渐变淡出效果 */
.fade-overlay {
  position: absolute;
  top: 0;
  right: 0;
  width: 30%; /* 覆盖右侧 30% 的区域 */
  height: 100%;
  /* 从透明渐变到纯白 */
  background: linear-gradient(to right, rgba(255, 255, 255, 0), #ffffff);
  z-index: 2;
}

/* 品牌内容区 */
.brand-content {
  position: relative;
  z-index: 3;
  text-align: center;
  margin-right: 50px; /* 稍微向左偏移一点，避开渐变区 */
}

.logo-wrapper {
  display: inline-flex;
  justify-content: center;
  align-items: center;
  width: 80px;
  height: 80px;
  background: #1890ff;
  border-radius: 16px;
  margin-bottom: 24px;
  box-shadow: 0 10px 20px rgba(24, 144, 255, 0.3);
}

.brand-icon {
  font-size: 48px;
  color: #fff;
}

.brand-title {
  font-size: 48px;
  font-weight: 800;
  color: #002140; /* 深蓝黑，与Layout侧边栏呼应 */
  margin-bottom: 8px;
  letter-spacing: 2px;
  text-shadow: 0 2px 10px rgba(0,0,0,0.05);
}

.brand-subtitle {
  font-size: 18px;
  color: #666;
  font-weight: 400;
  letter-spacing: 4px;
}

/* 已删除 .excel-cell-decoration 和 @keyframes float 相关样式 */

/* ================= 右侧设计 ================= */
.right-section {
  flex: 1; /* 占据剩余空间 */
  background: #ffffff; /* 纯白 */
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  position: relative;
  padding: 40px;
}

.login-box {
  width: 100%;
  max-width: 380px;
  padding: 0 20px;
  /* 不需要边框，保持纯净，或者加一点点阴影 */
}

.form-header {
  margin-bottom: 40px;
}

.form-header h2 {
  font-size: 32px;
  font-weight: 700;
  color: #1890ff;
  margin-bottom: 8px;
}

.form-header .sub-text {
  color: #999;
  font-size: 14px;
}

/* 输入框样式微调 - 增强蓝色边框感 */
:deep(.custom-input .ant-input-prefix) {
  margin-right: 10px;
}

:deep(.ant-input-affix-wrapper) {
  padding: 10px 11px;
  border-radius: 6px;
  border-color: #d9d9d9;
}

:deep(.ant-input-affix-wrapper:hover),
:deep(.ant-input-affix-wrapper:focus),
:deep(.ant-input-affix-wrapper-focused) {
  border-color: #1890ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.1);
}

.form-options {
  display: flex;
  justify-content: space-between;
  margin-bottom: 24px;
}

.forgot-password {
  color: #1890ff;
}

.login-btn {
  height: 48px;
  font-size: 16px;
  font-weight: 500;
  border-radius: 6px;
  background: #1890ff;
  box-shadow: 0 4px 14px rgba(24, 144, 255, 0.3);
  border: none;
}

.login-btn:hover {
  background: #40a9ff;
  box-shadow: 0 6px 20px rgba(24, 144, 255, 0.4);
}

.copyright {
  position: absolute;
  bottom: 24px;
  color: #ccc;
  font-size: 12px;
}

/* 响应式适配 */
@media (max-width: 900px) {
  .left-section {
    display: none; /* 小屏幕隐藏左侧 */
  }
}
</style>