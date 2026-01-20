<template>
  <div class="excel-preview-container">

    <div v-if="dataSource.length === 0" style="height: 100%; display: flex; flex-direction: column;">

      <div v-if="loading" class="loading-overlay">
        <a-spin tip="正在解析文件..." />
      </div>

      <div
          v-if="!readOnly"
          class="drop-zone"
          :class="{ 'is-dragging': isDragging }"
          @dragover.prevent="onDragOver"
          @dragleave.prevent="onDragLeave"
          @drop.prevent="onDrop"
      >
        <a-empty image="simple">
          <template #description>
            <div class="empty-text">
              <p>暂无数据，请先上传文件</p>
              <p class="sub-text">
                <cloud-upload-outlined /> 支持点击上方按钮或直接拖拽多个 Excel 文件至此
              </p>
            </div>
          </template>
        </a-empty>
      </div>

      <div v-else class="readonly-empty">
        <a-empty description="该文件暂无预览数据或解析中..." />
      </div>
    </div>

    <a-table
        v-else
        :columns="columns"
        :data-source="dataSource"
        :loading="loading"
        :scroll="{ x: 'max-content', y: 500 }"
        :pagination="false"
        size="small"
        bordered
        row-key="index"
    />
  </div>
</template>

<script setup>
import { ref, defineExpose, defineEmits, defineProps } from 'vue';
import { CloudUploadOutlined } from '@ant-design/icons-vue';
import { message } from 'ant-design-vue';

// 🟢 新增：接收 readOnly 属性，默认为 false
const props = defineProps({
  readOnly: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['onFileDrop']);

const columns = ref([]);
const dataSource = ref([]);
const loading = ref(false);
const isDragging = ref(false);

const onDragOver = () => { if (!props.readOnly) isDragging.value = true; };
const onDragLeave = () => { if (!props.readOnly) isDragging.value = false; };

const onDrop = (e) => {
  if (props.readOnly) return; // 🟢 只读模式下禁用拖拽

  isDragging.value = false;
  const files = Array.from(e.dataTransfer.files);
  if (files.length === 0) return;

  const excelFiles = files.filter(file =>
      file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' ||
      file.type === 'application/vnd.ms-excel' ||
      file.name.endsWith('.xlsx') ||
      file.name.endsWith('.xls')
  );

  if (excelFiles.length === 0) {
    message.error('仅支持上传 Excel 文件');
    return;
  }

  loading.value = true;
  emit('onFileDrop', excelFiles);
};

const updateData = (newColumns, newData) => {
  loading.value = true;
  // 模拟一点延迟，让 loading 闪烁一下以提示用户刷新了
  setTimeout(() => {
    columns.value = newColumns || [];
    dataSource.value = (newData || []).map((item, index) => ({ ...item, index }));
    loading.value = false;
  }, 200);
};

defineExpose({
  updateData,
  loading
});
</script>

<style scoped>
.excel-preview-container {
  height: 100%;
  overflow: hidden;
  padding: 10px;
  display: flex;
  flex-direction: column;
  position: relative;
}

.loading-overlay {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  z-index: 10;
  background: rgba(255,255,255,0.8);
  display: flex;
  justify-content: center;
  align-items: center;
}

.drop-zone {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  border: 2px dashed #d9d9d9;
  border-radius: 8px;
  background: #fafafa;
  transition: all 0.3s;
  margin-top: 20px;
  min-height: 300px;
  cursor: pointer;
}

.drop-zone.is-dragging {
  border-color: #1890ff;
  background: #e6f7ff;
}

.readonly-empty {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
  color: #999;
}

.empty-text { color: #666; font-size: 14px; }
.sub-text { font-size: 12px; color: #999; margin-top: 8px; }
</style>