<template>
  <div class="uploader-wrapper">
    <a-upload
        name="file"
        :multiple="true"
        :show-upload-list="false"
        :before-upload="handleBeforeUpload"
        :custom-request="dummyRequest"
        accept=".xlsx, .xls"
    >
      <a-button type="primary" :loading="uploading" class="upload-btn">
        <template #icon><cloud-upload-outlined /></template>
        {{ uploading ? '正在处理...' : '点击或拖拽上传 Excel' }}
      </a-button>
    </a-upload>

    <a-modal
        v-model:visible="batchModalVisible"
        title="📚 批量文件处理向导"
        ok-text="确认并上传"
        cancel-text="取消"
        width="600px"
        :mask-closable="false"
        @ok="confirmBatchUpload"
        @cancel="clearPendingFiles"
    >
      <div class="file-summary-box">
        <div class="summary-header">
          <file-excel-outlined style="font-size: 18px; color: #1890ff; margin-right: 8px;" />
          <span>已捕获 <strong>{{ pendingFiles.length }}</strong> 个文件待处理</span>
        </div>
        <div class="file-scroll-list">
          <a-tag v-for="(f, index) in pendingFiles.slice(0, 5)" :key="index" color="blue" style="margin: 4px">
            {{ f.name }}
          </a-tag>
          <a-tag v-if="pendingFiles.length > 5" color="default" style="margin: 4px">
            ...以及其他 {{ pendingFiles.length - 5 }} 个文件
          </a-tag>
        </div>
      </div>

      <a-divider style="margin: 20px 0 15px 0">💡 请选择数据处理模式</a-divider>

      <div class="mode-selection">

        <div
            class="mode-card"
            :class="{ 'active': isMergeMode === true }"
            @click="isMergeMode = true"
        >
          <div class="radio-circle">
            <div class="inner-dot" v-if="isMergeMode === true"></div>
          </div>
          <div class="card-content">
            <div class="card-title">🔗 智能合并 (同构表)</div>
            <div class="card-desc">
              要求所有文件<b>列名一致</b>。系统将自动把它们拼接成一张总表。
              <br/><span style="color: #888; font-size: 12px;">(场景：汇总 1-12 月的销售报表)</span>
            </div>
          </div>
        </div>

        <div
            class="mode-card"
            :class="{ 'active': isMergeMode === false }"
            @click="isMergeMode = false"
        >
          <div class="radio-circle">
            <div class="inner-dot" v-if="isMergeMode === false"></div>
          </div>
          <div class="card-content">
            <div class="card-title">📂 保持独立 (异构表/多表关联)</div>
            <div class="card-desc">
              允许<b>不同列结构</b>的文件批量上传。文件将分别存入库中。
              <br/><span style="color: #1890ff; font-weight: 500; font-size: 12px;">(场景：上传"工资表"和"考勤表"，稍后在列表中勾选进行关联分析)</span>
            </div>
          </div>
        </div>

      </div>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, defineExpose } from 'vue';
import { message } from 'ant-design-vue';
import { CloudUploadOutlined, FileExcelOutlined } from '@ant-design/icons-vue';
import request from '../utils/request';

// 定义事件
const emit = defineEmits(['uploadSuccess']);

// 状态
const uploading = ref(false);
const pendingFiles = ref([]); // 待处理文件队列
const batchModalVisible = ref(false);
const isMergeMode = ref(true); // 默认开启合并

let timer = null; // 防抖定时器

// 1. 占位函数
const dummyRequest = ({ onSuccess }) => {
  setTimeout(() => { onSuccess("ok"); }, 0);
};

// 2. 核心拦截逻辑：用户点击按钮选择文件后触发
const handleBeforeUpload = (file) => {
  pendingFiles.value.push(file);

  if (timer) clearTimeout(timer);
  timer = setTimeout(() => {
    processPendingFiles();
  }, 100);

  return false;
};

// 🟢 处理外部（拖拽）传入的文件列表
const handleExternalFiles = (files) => {
  if (!files || files.length === 0) return;
  // 直接覆盖或追加到队列
  pendingFiles.value = [...files];
  // 立即触发处理流程
  processPendingFiles();
};

// 3. 处理文件队列 (通用逻辑)
const processPendingFiles = () => {
  if (pendingFiles.value.length === 0) return;

  // 场景 A: 单个文件 -> 直接上传
  if (pendingFiles.value.length === 1) {
    doSingleUpload(pendingFiles.value[0]);
  }
  // 场景 B: 多个文件 -> 弹出选项框
  else {
    // 这里可以根据需求调整默认值，如果你的用户更常用多表关联，可以设为 false
    isMergeMode.value = true;
    batchModalVisible.value = true;
  }
};

// 4. 执行单文件上传
const doSingleUpload = async (file) => {
  const formData = new FormData();
  formData.append('file', file);

  uploading.value = true;
  pendingFiles.value = []; // 清空

  try {
    const res = await request.post('/api/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });

    const fileId = res.file_id || (res.data && res.data.file_id) || res.id;

    if (fileId) {
      message.success('上传成功');
      emit('uploadSuccess', [{
        file_id: fileId,
        filename: file.name
      }]);
    } else {
      message.error('上传返回值异常');
    }
  } catch (e) {
    console.error(e);
    message.error('上传失败: ' + (e.message || '未知错误'));
  } finally {
    uploading.value = false;
  }
};

// 5. 执行批量上传
const confirmBatchUpload = async () => {
  if (pendingFiles.value.length === 0) return;

  batchModalVisible.value = false;
  uploading.value = true;

  const formData = new FormData();
  // 循环 append 多个文件
  pendingFiles.value.forEach(file => {
    formData.append('files', file);
  });
  // 传递用户选择的模式
  formData.append('auto_merge', isMergeMode.value);

  try {
    const res = await request.post('/api/upload/batch', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });

    // 兼容后端直接返回 dict 或 data 字段
    const data = res.data || res;

    // 模式 A：后端进行了合并，只返回 1 个文件结果
    if (data.mode === 'merge') {
      message.success(data.msg);
      emit('uploadSuccess', [{
        file_id: data.file_info.file_id,
        filename: data.file_info.filename
      }]);
    }
    // 模式 B：后端保持独立，返回 N 个文件列表
    else {
      message.success(data.msg);
      // data.files 是一个列表 [{file_id: 1, ...}, {file_id: 2, ...}]
      if (data.files && data.files.length > 0) {
        emit('uploadSuccess', data.files);
      }
    }

  } catch (e) {
    console.error(e);
    const errorMsg = e.response?.data?.detail || e.message || '批量上传失败';
    message.error(errorMsg);
  } finally {
    uploading.value = false;
    pendingFiles.value = [];
  }
};

const clearPendingFiles = () => {
  pendingFiles.value = [];
};

// 暴露方法给 Dashboard 调用
defineExpose({
  handleExternalFiles
});
</script>

<style scoped>
.uploader-wrapper {
  display: inline-block;
}

/* === 文件概览区域 === */
.file-summary-box {
  background-color: #f0f9ff;
  border: 1px solid #bae7ff;
  border-radius: 6px;
  padding: 12px;
}
.summary-header {
  display: flex;
  align-items: center;
  font-size: 14px;
  color: #000;
  margin-bottom: 8px;
}
.file-scroll-list {
  display: flex;
  flex-wrap: wrap;
  max-height: 80px;
  overflow-y: auto;
}

/* === 卡片式选择区 (核心优化) === */
.mode-selection {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.mode-card {
  display: flex;
  align-items: flex-start;
  padding: 16px;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: #fff;
  position: relative;
}

.mode-card:hover {
  border-color: #40a9ff;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.mode-card.active {
  border-color: #1890ff;
  background-color: #f0f5ff;
}

/* 模拟 Radio 按钮圆圈 */
.radio-circle {
  width: 18px;
  height: 18px;
  border: 2px solid #d9d9d9;
  border-radius: 50%;
  margin-right: 12px;
  margin-top: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff;
  flex-shrink: 0;
}

.mode-card.active .radio-circle {
  border-color: #1890ff;
}

.inner-dot {
  width: 8px;
  height: 8px;
  background: #1890ff;
  border-radius: 50%;
}

.card-content {
  flex: 1;
}

.card-title {
  font-weight: bold;
  font-size: 15px;
  color: #333;
  margin-bottom: 4px;
}

.card-desc {
  font-size: 13px;
  color: #888;
  line-height: 1.5;
}
</style>