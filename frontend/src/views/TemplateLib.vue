<template>
  <div class="lib-container">
    <div class="filter-bar">
      <div class="left-tools">
        <a-radio-group v-model:value="activeCategory" button-style="solid" size="large">
          <a-radio-button value="all">全部</a-radio-button>
          <a-radio-button value="计算">🧮 计算</a-radio-button>
          <a-radio-button value="清洗">🧹 清洗</a-radio-button>
          <a-radio-button value="统计">📊 统计</a-radio-button>
          <a-radio-button value="自定义">🛠 自定义</a-radio-button>
        </a-radio-group>
      </div>

      <div class="right-tools">
        <a-button type="primary" size="large" @click="openCreateModal" class="add-btn">
          <plus-outlined /> 添加模板
        </a-button>
        <a-input-search
            v-model:value="searchText"
            placeholder="搜索模板..."
            style="width: 260px"
            allow-clear
            size="large"
        />
      </div>
    </div>

    <a-divider style="margin: 20px 0" />

    <a-spin :spinning="loading" tip="正在加载模板库...">
      <div class="template-grid">
        <a-card
            v-for="tpl in filteredTemplates"
            :key="tpl.id"
            hoverable
            class="tpl-card"
        >
          <template #extra>
            <a-popconfirm
                title="确定要删除这个模板吗？"
                ok-text="删除"
                cancel-text="取消"
                @confirm="handleDelete(tpl)"
            >
              <a-button type="text" danger size="small" class="delete-btn">
                <delete-outlined />
              </a-button>
            </a-popconfirm>
          </template>

          <template #actions>
            <a-button type="link" @click.stop="openEditModal(tpl)">
              <edit-outlined /> 编辑
            </a-button>
            <a-button type="link" class="apply-btn" @click.stop="applyTemplate(tpl)">
              <rocket-outlined /> 应用
            </a-button>
          </template>

          <a-card-meta>
            <template #title>
              <div class="card-title">
                <span class="category-icon">{{ getCategoryIcon(tpl.category) }}</span>
                <span :title="tpl.title">{{ tpl.title }}</span>
              </div>
            </template>
            <template #description>
              <div class="tpl-desc" :title="tpl.description">
                {{ tpl.description }}
              </div>
              <div class="tpl-tag-row">
                <a-tag :color="getCategoryColor(tpl.category)">{{ tpl.category }}</a-tag>
              </div>
            </template>
          </a-card-meta>
        </a-card>
      </div>

      <a-empty v-if="!loading && filteredTemplates.length === 0" description="未找到匹配的模板" style="margin-top: 50px" />
    </a-spin>

    <a-modal
        v-model:visible="modalVisible"
        :title="isEditMode ? '✏️ 编辑模板' : '✨ 添加新模板'"
        @ok="handleSave"
        :confirmLoading="saving"
        width="600px"
    >
      <a-form layout="vertical">
        <a-row :gutter="16">
          <a-col :span="16">
            <a-form-item label="模板名称" required>
              <a-input v-model:value="currentTpl.title" placeholder="例如：提取邮箱地址" />
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="模板类别" required>
              <a-select v-model:value="currentTpl.category">
                <a-select-option value="计算">🧮 计算</a-select-option>
                <a-select-option value="清洗">🧹 清洗</a-select-option>
                <a-select-option value="统计">📊 统计</a-select-option>
                <a-select-option value="自定义">🛠 自定义</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>

        <a-form-item label="功能描述">
          <a-textarea v-model:value="currentTpl.description" :rows="2" placeholder="简要描述该模板的功能，显示在卡片上" />
        </a-form-item>

        <a-form-item label="AI 提示词 (Prompt)" required>
          <a-textarea
              v-model:value="currentTpl.prompt_text"
              :rows="5"
              placeholder="输入发送给 AI 的具体指令。&#10;例如：请将 A 列的日期格式转换为 YYYY-MM-DD"
          />
          <div style="font-size: 12px; color: #999; margin-top: 5px;">
            💡 技巧：指令越明确，AI 生成的 Python/Excel 公式越准确。
          </div>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { message, Modal } from 'ant-design-vue';
import {
  EditOutlined,
  RocketOutlined,
  PlusOutlined,
  DeleteOutlined
} from '@ant-design/icons-vue';
import request from '../utils/request';

const router = useRouter();

// --- 状态定义 ---
const templates = ref([]);
const loading = ref(false);
const activeCategory = ref('all');
const searchText = ref('');

// --- 模态框状态 ---
const modalVisible = ref(false);
const saving = ref(false);
const isEditMode = ref(false);
const currentTpl = ref({
  id: null,
  title: '',
  category: '自定义',
  description: '',
  prompt_text: ''
});

// --- 初始化加载 ---
const fetchTemplates = async () => {
  loading.value = true;
  try {
    const res = await request.get('/api/templates');
    templates.value = res.data || res;
  } catch (e) {
    console.error(e);
    message.error('加载模板库失败');
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  fetchTemplates();
});

// --- 计算属性：筛选逻辑 ---
const filteredTemplates = computed(() => {
  return templates.value.filter(t => {
    // 1. 分类筛选
    const matchCat = activeCategory.value === 'all' || t.category === activeCategory.value;
    // 2. 搜索筛选
    const lowerSearch = searchText.value.toLowerCase();
    const matchSearch = (t.title && t.title.toLowerCase().includes(lowerSearch)) ||
        (t.description && t.description.toLowerCase().includes(lowerSearch));
    return matchCat && matchSearch;
  });
});

// --- 辅助函数 ---
const getCategoryColor = (cat) => {
  if (cat === '计算') return 'cyan';
  if (cat === '清洗') return 'orange';
  if (cat === '统计') return 'purple';
  if (cat === '自定义') return 'geekblue';
  return 'blue';
};

const getCategoryIcon = (cat) => {
  if (cat === '计算') return '🧮';
  if (cat === '清洗') return '🧹';
  if (cat === '统计') return '📊';
  if (cat === '自定义') return '🛠';
  return '📝';
};

// --- 功能：立即应用 ---
const applyTemplate = (tpl) => {
  router.push({
    name: 'Dashboard',
    query: { prompt: tpl.prompt_text }
  });
  message.loading({ content: '正在跳转到工作台...', duration: 1 });
};

// --- 功能：添加模板 ---
const openCreateModal = () => {
  isEditMode.value = false;
  // 重置表单，默认选中自定义
  currentTpl.value = {
    id: null,
    title: '',
    category: '自定义',
    description: '',
    prompt_text: ''
  };
  modalVisible.value = true;
};

// --- 功能：编辑模板 ---
const openEditModal = (tpl) => {
  isEditMode.value = true;
  currentTpl.value = { ...tpl }; // 深拷贝
  modalVisible.value = true;
};

// --- 功能：保存 (新增/修改) ---
const handleSave = async () => {
  if (!currentTpl.value.title || !currentTpl.value.prompt_text) {
    return message.warning('名称和提示词不能为空');
  }

  saving.value = true;
  try {
    if (isEditMode.value) {
      // 编辑逻辑
      await request.put(`/api/templates/${currentTpl.value.id}`, currentTpl.value);
      message.success('模板更新成功');
    } else {
      // 新增逻辑
      await request.post('/api/templates', currentTpl.value);
      message.success('模板添加成功');
    }

    modalVisible.value = false;
    await fetchTemplates(); // 刷新列表
  } catch (e) {
    console.error(e);
    message.error('保存失败');
  } finally {
    saving.value = false;
  }
};

// --- 功能：删除模板 ---
const handleDelete = async (tpl) => {
  try {
    const res = await request.delete(`/api/templates/${tpl.id}`);
    if (res.success || res.msg) {
      message.success('模板已删除');
      // 这里的过滤比重新请求接口体验更好，更平滑
      templates.value = templates.value.filter(t => t.id !== tpl.id);
    }
  } catch (e) {
    console.error(e);
    message.error('删除失败');
  }
};
</script>

<style scoped>
.lib-container { padding: 20px; }
.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.right-tools {
  display: flex;
  gap: 12px;
}

/* 网格布局 */
.template-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 24px;
}

.tpl-card {
  border-radius: 12px;
  transition: all 0.3s ease;
  border: 1px solid #f0f0f0;
  position: relative;
}

.tpl-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 10px 20px rgba(0,0,0,0.08);
  border-color: #1890ff;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
}

.category-icon { font-size: 18px; }

.tpl-desc {
  height: 44px;
  overflow: hidden;
  color: #666;
  margin: 10px 0;
  font-size: 13px;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.tpl-tag-row { margin-top: 8px; }

.apply-btn { font-weight: bold; }
.delete-btn { color: #ccc; transition: color 0.3s; }
.delete-btn:hover { color: #ff4d4f; }

/* 覆盖 Ant Design 默认样式 */
:deep(.ant-card-actions li) { margin: 8px 0; }
:deep(.ant-card-actions a) { font-size: 13px; }
/* 调整卡片右上角 extra 的位置 */
:deep(.ant-card-extra) {
  margin-left: auto;
  padding: 16px 16px 0 0;
}
</style>