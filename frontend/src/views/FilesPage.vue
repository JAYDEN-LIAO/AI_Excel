<template>
  <div class="files-container">
    <div class="filter-bar">
      <div class="left-tools">
        <span class="title">🗂️ 表格管理</span>
        <span class="sub-text">左侧为原始上传数据，右侧为 AI 处理后的结果数据</span>
      </div>

      <div class="right-tools">
        <a-button type="primary" size="large" @click="fetchHistory">
          <reload-outlined /> 刷新列表
        </a-button>
        <a-input-search
            v-model:value="searchText"
            placeholder="搜索文件名..."
            style="width: 260px"
            allow-clear
            size="large"
            @search="fetchHistory"
        />
      </div>
    </div>

    <a-divider style="margin: 20px 0" />

    <div class="history-list">
      <a-spin :spinning="loading">
        <a-empty v-if="historyList.length === 0" description="暂无历史记录" />

        <div v-else class="list-content">
          <a-row :gutter="24" class="list-header">
            <a-col :span="11"><cloud-upload-outlined /> 原始上传表格</a-col>
            <a-col :span="2" style="text-align: center;"><arrow-right-outlined /></a-col>
            <a-col :span="11"><thunderbolt-filled /> AI 处理结果</a-col>
          </a-row>

          <div v-for="item in historyList" :key="item.id" class="history-item">
            <a-row :gutter="24" align="middle">

              <a-col :span="11">
                <a-card hoverable class="file-card original" size="small">
                  <div class="card-body">
                    <div class="icon-wrapper bg-blue">
                      <file-excel-outlined />
                    </div>
                    <div class="file-info">
                      <div class="filename" :title="item.original.filename">{{ item.original.filename }}</div>
                      <div class="meta">上传时间: {{ item.original.upload_time }}</div>
                    </div>
                    <div class="actions">
                      <a-tooltip title="在当前页预览数据">
                        <a-button type="text" size="small" @click="handlePreview(item.original)">
                          <eye-outlined /> 预览
                        </a-button>
                      </a-tooltip>
                      <a-tooltip title="前往工作台继续编辑">
                        <a-button type="text" size="small" class="text-blue" @click="handleEdit(item.original)">
                          <edit-outlined /> 编辑
                        </a-button>
                      </a-tooltip>
                    </div>
                  </div>
                </a-card>
              </a-col>

              <a-col :span="2" style="text-align: center;">
                <double-right-outlined style="color: #ccc;" />
              </a-col>

              <a-col :span="11">
                <a-card v-if="item.result" hoverable class="file-card result" size="small">
                  <div class="card-body">
                    <div class="icon-wrapper bg-green">
                      <check-circle-outlined />
                    </div>
                    <div class="file-info">
                      <div class="filename" :title="item.result.filename">{{ item.result.filename }}</div>
                      <div class="meta">处理时间: {{ item.result.generated_time }}</div>
                    </div>
                    <div class="actions">
                      <a-tooltip title="预览处理结果">
                        <a-button type="text" size="small" @click="handlePreview(item.result)">
                          <eye-outlined /> 预览
                        </a-button>
                      </a-tooltip>
                      <a-tooltip title="下载文件">
                        <a-button type="text" size="small" class="text-green" :href="item.result.download_url" :download="item.result.filename">
                          <download-outlined /> 下载
                        </a-button>
                      </a-tooltip>
                    </div>
                  </div>
                </a-card>

                <div v-else class="empty-placeholder">
                  <span>等待处理</span>
                </div>
              </a-col>

            </a-row>
          </div>
        </div>
      </a-spin>
    </div>

    <a-modal
        v-model:visible="previewVisible"
        :title="`📄 数据预览: ${previewTitle}`"
        width="1000px"
        :footer="null"
        destroyOnClose
    >
      <div style="height: 600px; overflow: hidden;">
        <ExcelPreview ref="previewRef" :read-only="true" />
      </div>
    </a-modal>

  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import { message } from 'ant-design-vue';
import request from '../utils/request';
import ExcelPreview from '../components/ExcelPreview.vue';
import {
  FileExcelOutlined, CloudUploadOutlined, ThunderboltFilled,
  ArrowRightOutlined, DoubleRightOutlined, CheckCircleOutlined,
  EyeOutlined, EditOutlined, DownloadOutlined, ReloadOutlined
} from '@ant-design/icons-vue';

const router = useRouter();
const loading = ref(false);
const searchText = ref('');
const historyList = ref([]);

// 预览相关
const previewVisible = ref(false);
const previewTitle = ref('');
const previewRef = ref(null);

// 1. 获取历史记录列表
const fetchHistory = async () => {
  loading.value = true;
  try {
    const res = await request.get('/api/history', { params: { q: searchText.value } });
    // 兼容多种返回结构
    const data = res.data || res;
    historyList.value = Array.isArray(data) ? data : [];
  } catch (e) {
    console.error(e);
    message.error('加载历史记录失败');
  } finally {
    loading.value = false;
  }
};

// 2. 预览逻辑 (已包含之前的修复)
const handlePreview = async (fileObj) => {
  if (!fileObj || !fileObj.file_id) return;

  previewTitle.value = fileObj.filename;
  previewVisible.value = true;

  await nextTick();

  if (previewRef.value) {
    previewRef.value.loading = true; // 开启加载转圈

    try {
      console.log(`正在请求文件预览: ID ${fileObj.file_id}`);

      const res = await request.get(`/api/files/${fileObj.file_id}/data`);

      let finalData = null;
      // 兼容性判断：优先取 columns 存在的层级
      if (res && res.columns) {
        finalData = res;
      } else if (res.data && res.data.columns) {
        finalData = res.data;
      } else {
        finalData = {};
      }

      const cols = finalData.columns || [];
      const rows = finalData.data || [];

      if (cols.length === 0) {
        message.warning("该文件似乎是空的，或者读取列失败");
      }

      previewRef.value.updateData(cols, rows);

    } catch (e) {
      console.error("预览请求失败:", e);
      message.error('无法加载预览数据');
      previewRef.value.loading = false;
    }
  }
};

// 3. 编辑逻辑
const handleEdit = (fileObj) => {
  router.push({
    name: 'Dashboard',
    query: {
      file_id: fileObj.file_id,
      filename: fileObj.filename
    }
  });
};

onMounted(() => {
  fetchHistory();
});
</script>

<style scoped>
.files-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 20px; /* 统一内边距 */
}

/* 顶部工具栏样式 - 与模板库保持一致 */
.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.left-tools {
  display: flex;
  flex-direction: column; /* 标题和副标题垂直排列 */
}

.right-tools {
  display: flex;
  gap: 12px; /* 按钮和搜索框之间的间距 */
}

.title {
  font-size: 18px;
  font-weight: bold;
  color: #333;
}

.sub-text {
  color: #999;
  font-size: 13px;
  margin-top: 4px;
}

/* 列表区域样式 */
.history-list { flex: 1; overflow-y: auto; padding-right: 5px; }
.list-header { font-weight: bold; color: #666; margin-bottom: 12px; padding: 0 10px; }
.history-item { margin-bottom: 16px; }

/* 卡片样式 */
.file-card { border-radius: 8px; transition: all 0.3s; border: 1px solid #f0f0f0; }
.file-card:hover { border-color: #1890ff; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
.file-card.result:hover { border-color: #52c41a; }

.card-body { display: flex; align-items: center; justify-content: space-between; }

.icon-wrapper { width: 40px; height: 40px; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-size: 20px; color: #fff; margin-right: 12px; flex-shrink: 0; }
.bg-blue { background: #1890ff; }
.bg-green { background: #52c41a; }

.file-info { flex: 1; overflow: hidden; }
.filename { font-weight: 600; color: #333; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-bottom: 4px; }
.meta { color: #999; font-size: 12px; }

.actions { display: flex; gap: 4px; }
.text-blue { color: #1890ff; }
.text-green { color: #52c41a; }

.empty-placeholder {
  height: 66px; border: 1px dashed #d9d9d9; border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  color: #ccc; font-size: 13px; background: #fafafa;
}

/* 滚动条美化 */
.history-list::-webkit-scrollbar { width: 6px; }
.history-list::-webkit-scrollbar-thumb { background: #ddd; border-radius: 3px; }
</style>