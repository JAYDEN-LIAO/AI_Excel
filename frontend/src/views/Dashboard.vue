<template>
  <div class="dashboard-container">

    <div class="status-bar">
      <div class="left-action">
        <ExcelUploader ref="uploaderRef" @uploadSuccess="handleBatchUploadSuccess" />
        <span v-if="fileList.length > 0" class="file-selector ml-3">
          <span class="mr-2">当前预览:</span>
          <a-select v-model:value="currentFileId" style="width: 250px" @change="handleFileSwitch">
            <a-select-option v-for="file in fileList" :key="file.file_id" :value="file.file_id">
              <file-excel-outlined /> {{ file.filename }}
            </a-select-option>
          </a-select>
          <a-tag color="blue" class="ml-2">{{ fileList.length }} 个文件待处理</a-tag>
        </span>
      </div>
      <div class="right-action">
        <a-button v-if="resultList.length === 1" type="primary" :href="resultList[0].url" :download="`处理结果_${resultList[0].filename}`">
          <download-outlined /> 下载结果
        </a-button>
        <a-dropdown v-if="resultList.length > 1">
          <template #overlay>
            <a-menu>
              <a-menu-item v-for="(res, index) in resultList" :key="index">
                <a :href="res.url" :download="`处理结果_${res.filename}`">
                  <download-outlined /> {{ res.filename }} (点击下载)
                </a>
              </a-menu-item>
            </a-menu>
          </template>
          <a-button type="primary">
            <download-outlined /> 批量下载 ({{ resultList.length }}) <down-outlined />
          </a-button>
        </a-dropdown>
      </div>
    </div>

    <a-divider style="margin: 16px 0" />

    <div class="workspace">
      <div class="data-panel">
        <div class="panel-header">
          <span>📊 数据实时预览 (Top 50)</span>
          <a-tooltip title="切换上方下拉框可预览不同文件">
            <question-circle-outlined style="color: #999; cursor: help;" />
          </a-tooltip>
        </div>
        <div class="table-wrapper">
          <ExcelPreview ref="previewRef" @onFileDrop="handleDragUpload" />
        </div>
      </div>

      <div class="ai-panel">

        <div class="panel-header ai-header">
          <a-segmented
              v-model:value="interactionMode"
              :options="[
                { label: '⚡ 执行操作', value: 'action' },
                { label: '💬 AI 咨询', value: 'chat' }
              ]"
              block
              style="width: 220px;"
          />
          <a-button type="link" size="small" @click="openTemplateModal">
            <appstore-outlined /> 打开公式库
          </a-button>
        </div>

        <div class="chat-window" ref="chatWindowRef">
          <transition name="fade" mode="out-in">

            <div v-if="interactionMode === 'action'" key="action" class="mode-container">

              <div v-if="!lastAiResult" class="welcome-box">
                <div class="icon-bg"><rocket-outlined /></div>
                <p>👋 选中文件，输入操作需求。</p>
                <p class="sub-text">AI 将自动生成公式并处理表格。</p>
                <div class="suggestion-chips">
                  <a-tag color="orange" @click="fillQuery('删除第2到第5行')">删除行</a-tag>
                  <a-tag color="cyan" @click="fillQuery('计算销售额（单价*数量）')">计算公式</a-tag>
                  <a-tag color="blue" @click="fillQuery('按年龄从大到小排序')">数据排序</a-tag>
                </div>
              </div>

              <transition name="slide-up">
                <div v-if="lastAiResult" class="result-card">
                  <div class="result-title">
                    <check-circle-filled style="color: #52c41a" />
                    <span>操作完成</span>
                  </div>

                  <div v-if="batchProgress.total > 1" class="mb-3" style="margin-bottom: 10px;">
                    <div style="display:flex; justify-content:space-between; font-size:12px; color:#666;">
                      <span>批量进度:</span>
                      <span>{{ batchProgress.current }} / {{ batchProgress.total }}</span>
                    </div>
                    <a-progress :percent="Math.floor((batchProgress.current / batchProgress.total) * 100)" size="small" status="active" />
                  </div>

                  <div class="code-block formula-highlight" v-if="lastAiResult.formula && lastAiResult.formula !== 'N/A'">
                    <div class="code-header">
                      <span class="label-text">⚡ 动态数组公式 (一步到位):</span>
                      <a-tooltip title="点击复制公式">
                        <a-button type="text" size="small" @click="copyText(lastAiResult.formula)">
                          <template #icon><copy-outlined /></template>
                          复制
                        </a-button>
                      </a-tooltip>
                    </div>
                    <div class="code-content" style="max-height: 120px; overflow-y: auto; white-space: pre-wrap; word-break: break-all;">
                      {{ lastAiResult.formula }}
                    </div>
                  </div>

                  <div v-if="lastAiResult.column_formulas && Object.keys(lastAiResult.column_formulas).length > 0"
                       style="margin-top: 15px; border-top: 1px dashed #eee; padding-top: 10px;">

                    <div style="font-size: 13px; font-weight: bold; color: #666; margin-bottom: 8px;">
                      📑 分列公式 (拖拽填充 Row 2):
                    </div>

                    <div style="display: flex; flex-direction: column; gap: 8px; max-height: 200px; overflow-y: auto;">
                      <div v-for="(formula, colName) in lastAiResult.column_formulas" :key="colName"
                           style="background: #f9f9f9; border: 1px solid #e8e8e8; border-radius: 4px; padding: 6px 10px; display: flex; align-items: flex-start; justify-content: space-between;">

                        <div style="display: flex; align-items: flex-start; overflow: hidden; flex: 1; min-width: 0;">
                          <a-tag color="blue" style="margin-right: 8px; flex-shrink: 0; margin-top: 2px;">{{ colName }}</a-tag>

                          <code style="font-family: monospace; color: #eb2f96; font-size: 12px; white-space: pre-wrap; word-break: break-all; overflow-wrap: break-word; line-height: 1.4;">
                            {{ formula }}
                          </code>
                        </div>

                        <a-tooltip title="复制此单元格公式">
                          <a-button type="text" size="small" @click="copyText(formula)" style="margin-left: 5px; flex-shrink: 0;">
                            <copy-outlined style="color: #999" />
                          </a-button>
                        </a-tooltip>
                      </div>
                    </div>
                  </div>
                  <div class="analysis-text" style="margin-top: 12px;">
                    💡 {{ lastAiResult.explanation || '执行完毕，请在右上角下载结果。' }}
                  </div>
                </div>
              </transition>
            </div>

            <div v-else key="chat" class="mode-container chat-mode">
              <div v-if="chatHistory.length === 0" class="welcome-box">
                <div class="icon-bg blue"><comment-outlined /></div>
                <p>我是您的数据分析助手。</p>
                <p class="sub-text">我可以帮您分析趋势、解释字段或提供建议，不会修改文件。</p>
              </div>

              <div class="chat-list">
                <div v-for="(msg, index) in chatHistory" :key="index" :class="['chat-bubble', msg.role]">
                  <div class="bubble-avatar">
                    <a-avatar v-if="msg.role === 'ai'" style="background-color: #1890ff" size="small">AI</a-avatar>
                    <a-avatar v-else style="background-color: #f56a00" size="small">Me</a-avatar>
                  </div>
                  <div class="bubble-content">
                    <div class="bubble-text" style="white-space: pre-wrap;">{{ msg.content }}</div>
                    <div v-if="msg.loading" class="typing-indicator">
                      <span></span><span></span><span></span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

          </transition>
        </div>

        <div class="input-area">
          <a-textarea
              v-model:value="userQuery"
              :placeholder="inputPlaceholder"
              :rows="3"
              @pressEnter="handleEnterPress"
          />

          <div class="action-bar">
            <div class="left-opts">
              <a-checkbox
                  v-if="interactionMode === 'action' && fileList.length > 1"
                  v-model:checked="applyToAll"
              >
                应用到所有文件
              </a-checkbox>
            </div>

            <a-button
                type="primary"
                :loading="generating"
                @click="handleMainAction"
                :class="{ 'chat-btn': interactionMode === 'chat' }"
            >
              <template #icon>
                <rocket-outlined v-if="interactionMode === 'action'" />
                <send-outlined v-else />
              </template>
              {{ interactionMode === 'action' ? '执行操作' : '发送咨询' }}
            </a-button>
          </div>
        </div>
      </div>
    </div>

    <a-modal
        v-model:visible="templateVisible"
        width="800px"
        :footer="null"
        :bodyStyle="{ padding: '0', height: '520px', overflow: 'hidden' }"
    >
      <template #title>
        <div style="display: flex; justify-content: space-between; align-items: center; padding-right: 30px;">
          <span>📚 公式能力库</span>
          <a-segmented v-model:value="libraryMode" :options="['AI 场景模板', 'Excel 原生函数']" />
        </div>
      </template>

      <div class="library-container">
        <div v-if="libraryMode === 'AI 场景模板'" class="scroll-area">
          <div style="padding: 0 20px;">
            <a-tabs v-model:activeKey="activeCategory">
              <a-tab-pane key="all" tab="全部" />
              <a-tab-pane key="计算" tab="🧮 计算" />
              <a-tab-pane key="清洗" tab="🧹 清洗" />
              <a-tab-pane key="统计" tab="📊 统计" />
              <a-tab-pane key="自定义" tab="🔨 自定义" />
            </a-tabs>

            <a-list :grid="{ gutter: 16, column: 2 }" :data-source="filteredTemplates">
              <template #renderItem="{ item }">
                <a-list-item>
                  <a-card hoverable size="small" @click="applyAiTemplate(item)" class="template-card">
                    <template #title><span style="font-size: 14px; font-weight: bold">{{ item.title }}</span></template>
                    <p class="template-desc">{{ item.description }}</p>
                    <div class="template-footer">
                      <a-tag :color="getCategoryColor(item.category)">{{ item.category }}</a-tag>
                      <span class="use-btn">应用 →</span>
                    </div>
                  </a-card>
                </a-list-item>
              </template>
            </a-list>
          </div>
        </div>

        <div v-else class="excel-mode-container">
          <a-tabs tab-position="left" style="height: 100%;">
            <a-tab-pane v-for="(funcs, category) in excelFunctions" :key="category" :tab="category">
              <div class="func-list-scroll">
                <a-list item-layout="horizontal" :data-source="funcs">
                  <template #renderItem="{ item }">
                    <a-list-item>
                      <a-list-item-meta>
                        <template #title>
                          <div class="func-item-header">
                            <a-tag color="blue" style="font-weight:bold; font-size:13px;">{{ item.name }}</a-tag>
                            <span class="func-desc">{{ item.desc }}</span>
                          </div>
                        </template>
                        <template #description>
                          <div class="syntax-box" @click="copyText(item.syntax)" title="点击复制">
                            <code>{{ item.syntax }}</code>
                            <copy-outlined class="copy-icon" />
                          </div>
                        </template>
                      </a-list-item-meta>
                    </a-list-item>
                  </template>
                </a-list>
              </div>
            </a-tab-pane>
          </a-tabs>
        </div>
      </div>
    </a-modal>

  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, watch } from 'vue';
import { useRoute } from 'vue-router';
import { message } from 'ant-design-vue';
import ExcelUploader from '../components/ExcelUploader.vue';
import ExcelPreview from '../components/ExcelPreview.vue';
import request from '../utils/request';
import {
  FileExcelOutlined, DownloadOutlined, QuestionCircleOutlined,
  RobotFilled, RocketOutlined, CheckCircleFilled,
  AppstoreOutlined, DownOutlined, CommentOutlined, SendOutlined,
  CopyOutlined // 引入复制图标
} from '@ant-design/icons-vue';

// --- 路由初始化 ---
const route = useRoute();

// --- 状态管理 ---
const fileList = ref([]);
const currentFileId = ref(null);
const resultList = ref([]);
const lastAiResult = ref(null);
const applyToAll = ref(false);
const batchProgress = ref({ current: 0, total: 0 });

const userQuery = ref('');
const generating = ref(false);

// 交互模式: 'action' | 'chat'
const interactionMode = ref('action');
const chatHistory = ref([]);
const chatWindowRef = ref(null);

const previewRef = ref(null);
const uploaderRef = ref(null);

// --- 模板库相关状态 ---
const templateVisible = ref(false);
const allTemplates = ref([]);
const activeCategory = ref('all');
const libraryMode = ref('AI 场景模板');

// --- 原生 Excel 函数库数据 (补全数据) ---
// --- 原生 Excel 函数库数据 (全面扩充版) ---
const excelFunctions = ref({
  '热门高频': [
    { name: 'VLOOKUP', desc: '按列查找数据（职场必备）', syntax: '=VLOOKUP(H2, A:C, 3, 0)' },
    { name: 'XLOOKUP', desc: '新一代查找函数，替代 VLOOKUP', syntax: '=XLOOKUP(查找值, 查找列, 结果列)' },
    { name: 'IF', desc: '根据条件返回不同值', syntax: '=IF(B2>=60, "及格", "挂科")' },
    { name: 'SUMIFS', desc: '多条件求和', syntax: '=SUMIFS(求和区, 条件区1, 条件1, ...)' },
    { name: 'COUNTIF', desc: '统计满足条件的个数', syntax: '=COUNTIF(A:A, "已完成")' },
    { name: 'IFERROR', desc: '容错处理，如果错误则显示指定内容', syntax: '=IFERROR(A1/B1, 0)' },
    { name: 'TEXT', desc: '将数值转换为指定格式文本', syntax: '=TEXT(A1, "yyyy-mm-dd")' }
  ],
  '逻辑判断': [
    { name: 'IF', desc: '基础条件判断', syntax: '=IF(A1>0, "正数", "非正数")' },
    { name: 'IFS', desc: '多条件判断（避免嵌套 IF）', syntax: '=IFS(A1>90,"优", A1>80,"良", TRUE,"差")' },
    { name: 'IFERROR', desc: '捕获公式错误并自定义返回', syntax: '=IFERROR(VLOOKUP(...), "查无此人")' },
    { name: 'AND', desc: '所有条件为真时返回 TRUE', syntax: '=IF(AND(A1>0, B1>0), "双正", "")' },
    { name: 'OR', desc: '任一条件为真时返回 TRUE', syntax: '=IF(OR(A1>0, B1>0), "有正", "")' },
    { name: 'NOT', desc: '对逻辑值求反', syntax: '=NOT(A1="完成")' },
    { name: 'ISBLANK', desc: '判断单元格是否为空', syntax: '=IF(ISBLANK(A1), "缺考", A1)' },
    { name: 'ISNUMBER', desc: '判断是否为数字', syntax: '=ISNUMBER(A1)' }
  ],
  '查找引用': [
    { name: 'VLOOKUP', desc: '纵向查找（最常用）', syntax: '=VLOOKUP(lookup_value, table, col_index, 0)' },
    { name: 'HLOOKUP', desc: '横向查找', syntax: '=HLOOKUP(lookup_value, table, row_index, 0)' },
    { name: 'XLOOKUP', desc: '现代查找函数（Office 2021+）', syntax: '=XLOOKUP(找谁, 在哪找, 返回谁)' },
    { name: 'MATCH', desc: '返回指定项在区域中的位置', syntax: '=MATCH("张三", A:A, 0)' },
    { name: 'INDEX', desc: '返回区域中指定行列的值', syntax: '=INDEX(A1:C10, 2, 3)' },
    { name: 'INDEX+MATCH', desc: '强大的双向查找组合', syntax: '=INDEX(C:C, MATCH(A1, B:B, 0))' },
    { name: 'UNIQUE', desc: '提取唯一值（去重）', syntax: '=UNIQUE(A2:A100)' },
    { name: 'OFFSET', desc: '偏移引用（动态图表常用）', syntax: '=OFFSET(A1, 1, 2)' },
    { name: 'INDIRECT', desc: '将文本字符串转换为引用', syntax: '=INDIRECT("Sheet2!A1")' },
    { name: 'TRANSPOSE', desc: '行列转置', syntax: '=TRANSPOSE(A1:B5)' }
  ],
  '文本处理': [
    { name: 'LEFT', desc: '从左侧提取字符', syntax: '=LEFT(A1, 3)' },
    { name: 'RIGHT', desc: '从右侧提取字符', syntax: '=RIGHT(A1, 4)' },
    { name: 'MID', desc: '从中间提取字符', syntax: '=MID(身份证号, 7, 8)' },
    { name: 'LEN', desc: '计算文本长度', syntax: '=LEN(A1)' },
    { name: 'TRIM', desc: '清除多余空格', syntax: '=TRIM(A1)' },
    { name: 'CONCAT', desc: '连接文本', syntax: '=CONCAT(A1, B1, C1)' },
    { name: 'TEXTJOIN', desc: '用分隔符连接文本', syntax: '=TEXTJOIN("、", TRUE, A1:A10)' },
    { name: 'SUBSTITUTE', desc: '替换文本中的字符', syntax: '=SUBSTITUTE(A1, "旧", "新")' },
    { name: 'REPLACE', desc: '按位置替换文本', syntax: '=REPLACE(手机号, 4, 4, "****")' },
    { name: 'FIND', desc: '查找字符位置（区分大小写）', syntax: '=FIND("@", 邮箱地址)' },
    { name: 'UPPER/LOWER', desc: '转大写/转小写', syntax: '=UPPER(A1)' }
  ],
  '日期时间': [
    { name: 'TODAY', desc: '返回当前日期', syntax: '=TODAY()' },
    { name: 'NOW', desc: '返回当前日期和时间', syntax: '=NOW()' },
    { name: 'DATE', desc: '根据年月日构建日期', syntax: '=DATE(2023, 12, 31)' },
    { name: 'YEAR/MONTH/DAY', desc: '提取年、月、日', syntax: '=YEAR(A1)' },
    { name: 'DATEDIF', desc: '计算两个日期间隔（隐藏函数）', syntax: '=DATEDIF(开始, 结束, "Y")' },
    { name: 'EDATE', desc: '计算 N 个月后的日期', syntax: '=EDATE(A1, 3)' },
    { name: 'EOMONTH', desc: '计算某月最后一天', syntax: '=EOMONTH(A1, 0)' },
    { name: 'WEEKDAY', desc: '返回星期几（数字）', syntax: '=WEEKDAY(A1, 2)' },
    { name: 'WORKDAY', desc: '计算 N 个工作日后的日期', syntax: '=WORKDAY(A1, 5)' }
  ],
  '统计分析': [
    { name: 'COUNT', desc: '统计数字个数', syntax: '=COUNT(A:A)' },
    { name: 'COUNTA', desc: '统计非空单元格个数', syntax: '=COUNTA(A:A)' },
    { name: 'COUNTIF', desc: '单条件计数', syntax: '=COUNTIF(部门列, "销售部")' },
    { name: 'COUNTIFS', desc: '多条件计数', syntax: '=COUNTIFS(部门, "销售", 状态, "在职")' },
    { name: 'SUMIF', desc: '单条件求和', syntax: '=SUMIF(部门列, "销售部", 薪资列)' },
    { name: 'AVERAGEIF', desc: '单条件平均值', syntax: '=AVERAGEIF(性别, "男", 分数)' },
    { name: 'MAX/MIN', desc: '最大值/最小值', syntax: '=MAX(A:A)' },
    { name: 'LARGE', desc: '第 K 个最大值', syntax: '=LARGE(A:A, 3)' },
    { name: 'RANK', desc: '计算排名', syntax: '=RANK(A2, A:A)' },
    { name: 'MEDIAN', desc: '中位数', syntax: '=MEDIAN(A:A)' }
  ],
  '数学计算': [
    { name: 'SUM', desc: '求和', syntax: '=SUM(A1:A10)' },
    { name: 'ROUND', desc: '四舍五入', syntax: '=ROUND(A1, 2)' },
    { name: 'ROUNDUP', desc: '向上取整', syntax: '=ROUNDUP(A1, 0)' },
    { name: 'ROUNDDOWN', desc: '向下取整', syntax: '=ROUNDDOWN(A1, 0)' },
    { name: 'INT', desc: '取整（直接舍去小数）', syntax: '=INT(A1)' },
    { name: 'MOD', desc: '求余数', syntax: '=MOD(10, 3)' },
    { name: 'ABS', desc: '绝对值', syntax: '=ABS(A1-B1)' },
    { name: 'RAND', desc: '生成 0-1 随机数', syntax: '=RAND()' },
    { name: 'RANDBETWEEN', desc: '生成范围内的随机整数', syntax: '=RANDBETWEEN(1, 100)' },
    { name: 'PRODUCT', desc: '乘积', syntax: '=PRODUCT(A1:C1)' }
  ]
});

// --- 页面加载 ---
onMounted(async () => {
  const { file_id, filename, prompt } = route.query;
  if (prompt) userQuery.value = prompt;

  if (file_id) {
    let existingFile = fileList.value.find(f => f.file_id === file_id);
    if (!existingFile) {
      existingFile = { file_id: file_id, filename: filename || `文件-${file_id}` };
      fileList.value.unshift(existingFile);
    }
    currentFileId.value = file_id;
    await loadPreviewData(file_id);
  }
});

// --- 计算属性 ---
const inputPlaceholder = computed(() => {
  return interactionMode.value === 'action'
      ? "例如：删除所有年龄小于18岁的行..."
      : "例如：帮我分析一下销售额的趋势...";
});

// --- 工具函数：复制文本 ---
const copyText = (text) => {
  if (!text) return;
  navigator.clipboard.writeText(text).then(() => {
    message.success('已复制到剪贴板');
  }).catch(() => {
    message.error('复制失败');
  });
};

const scrollToBottom = () => {
  nextTick(() => {
    if (chatWindowRef.value) {
      chatWindowRef.value.scrollTop = chatWindowRef.value.scrollHeight;
    }
  });
};

// --- 交互入口 ---
const handleEnterPress = (e) => {
  if (!e.shiftKey) {
    e.preventDefault();
    handleMainAction();
  }
}

const handleMainAction = () => {
  if (interactionMode.value === 'action') {
    handleGenerate();
  } else {
    handleChatSubmit();
  }
};

// --- 业务逻辑：Chat ---
const handleChatSubmit = async () => {
  if (!userQuery.value.trim()) return message.warning('请输入问题');
  if (fileList.value.length === 0) return message.warning('请先上传文件');

  const question = userQuery.value;
  userQuery.value = '';

  chatHistory.value.push({ role: 'user', content: question });
  scrollToBottom();

  const aiMsgIndex = chatHistory.value.push({ role: 'ai', content: '', loading: true }) - 1;
  scrollToBottom();
  generating.value = true;

  try {
    const res = await request.post('/api/chat', {
      file_id: currentFileId.value,
      query: question
    });
    chatHistory.value[aiMsgIndex].loading = false;
    chatHistory.value[aiMsgIndex].content = res.data?.answer || res.answer || "AI 没有回应";
  } catch (e) {
    chatHistory.value[aiMsgIndex].loading = false;
    chatHistory.value[aiMsgIndex].content = "⚠️ 咨询出错，请稍后重试。";
  } finally {
    generating.value = false;
    scrollToBottom();
  }
};

// --- 业务逻辑：Generate Action ---
// --- 业务逻辑：Generate Action (已修正多表逻辑) ---
const handleGenerate = async () => {
  if (!userQuery.value.trim()) return message.warning('请输入需求');
  if (fileList.value.length === 0) return message.warning('请先上传文件');

  generating.value = true;
  lastAiResult.value = null;
  resultList.value = [];

  // 1. 判断是否触发多表模式
  const isMultiFileMode = applyToAll.value && fileList.value.length > 1;

  try {
    if (isMultiFileMode) {
      // ============================================
      // 🚀 分支 A: 多表关联模式 (调用 process_multi_files)
      // ============================================
      message.loading({ content: '正在进行多表联合分析...', key: 'process_loading' });

      // 收集所有文件 ID
      const allFileIds = fileList.value.map(f => f.file_id);

      const res = await request.post('/api/process_multi_files', {
        file_ids: allFileIds,
        query: userQuery.value
      });

      const rData = res.data || res; // 兼容不同响应结构

      if (rData.success) {
        message.success({ content: '多表处理成功！', key: 'process_loading' });

        // 1. 添加下载链接
        resultList.value.push({
          filename: '多表合并结果.xlsx',
          url: `http://127.0.0.1:8000${rData.download_url}`
        });

        // 2. 显示 AI 结果反馈 (🔥🔥🔥 核心修改处 🔥🔥🔥)
        // 优先使用后端返回的 raw_result，这样才能显示 AI 生成的复杂公式
        if (rData.raw_result) {
          lastAiResult.value = {
            action_type: rData.raw_result.action_type || 'multi_merge',
            // 长公式 (用于 A1 溢出)
            formula: rData.raw_result.excel_formula || 'Python Pandas Merge',
            // 🟢 短公式字典 (用于拖拽) - 接收后端传回的数据
            column_formulas: rData.raw_result.column_formulas || {},
            explanation: rData.raw_result.explanation || '多表数据关联与计算完成。'
          };
        } else {
          // 兜底逻辑
          lastAiResult.value = {
            action_type: 'multi_merge',
            formula: 'Python Pandas Merge',
            column_formulas: {}, // 兜底空对象
            explanation: '已根据您的需求，完成多表数据的关联、计算与合并。请点击上方按钮下载最终结果。'
          };
        }

        // (可选) 自动预览逻辑...
        if (rData.file_id) {
          // await loadPreviewData(rData.file_id);
        }

      } else {
        message.error({ content: `处理失败: ${rData.msg}`, key: 'process_loading' });
      }

    } else {
      // ============================================
      // 🐢 分支 B: 单表处理模式 (保持不变)
      // ============================================
      let targetFiles = [];

      if (applyToAll.value) {
        targetFiles = fileList.value;
      } else {
        const current = fileList.value.find(f => f.file_id === currentFileId.value);
        if (current) targetFiles = [current];
      }

      batchProgress.value = { current: 0, total: targetFiles.length };

      for (const file of targetFiles) {
        try {
          const res = await request.post('/api/generate_formula', {
            file_id: file.file_id,
            query: userQuery.value
          });
          const rData = res.data || res;

          if (rData.success) {
            resultList.value.push({
              filename: file.filename,
              url: `http://127.0.0.1:8000${rData.download_url}`
            });

            if (file.file_id === currentFileId.value) {
              if (rData.preview_data && previewRef.value) {
                previewRef.value.updateData(rData.preview_data.columns, rData.preview_data.dataSource);
              }
              const raw = rData.raw_result || {};
              lastAiResult.value = {
                action_type: raw.action_type,
                formula: raw.excel_formula || 'N/A',
                // 单表模式通常没有这个字段，给空即可
                column_formulas: {},
                explanation: raw.explanation || '操作成功'
              };
            }
          } else {
            message.error(`${file.filename} 处理失败: ${rData.msg}`);
          }
        } catch (innerE) {
          console.error(innerE);
          message.error(`${file.filename} 请求出错`);
        }
        batchProgress.value.current++;
      }
    }
  } catch (e) {
    console.error(e);
    message.error('系统执行错误');
  } finally {
    generating.value = false;
  }
};
const handleBatchUploadSuccess = async (uploadedFiles) => {
  fileList.value = uploadedFiles;
  resultList.value = [];
  lastAiResult.value = null;
  if (fileList.value.length > 0) {
    currentFileId.value = fileList.value[0].file_id;
    await loadPreviewData(currentFileId.value);
  }
};

const handleFileSwitch = async (val) => await loadPreviewData(val);

const loadPreviewData = async (fileId) => {
  const fileObj = fileList.value.find(f => f.file_id === fileId);
  try {
    const res = await request.get(`/api/files/${fileId}/data`);
    const dataObj = res.data || res;
    if (previewRef.value) {
      previewRef.value.updateData(dataObj.columns || res.columns, dataObj.data || res.data);
    }
  } catch (e) { message.error(`预览加载失败`); }
};

const handleDragUpload = (files) => {
  if (uploaderRef.value) uploaderRef.value.handleExternalFiles(files);
};

const fillQuery = (text) => userQuery.value = text;

// --- 模板库逻辑 ---
const openTemplateModal = async () => {
  templateVisible.value = true;
  interactionMode.value = 'action';

  if (allTemplates.value.length === 0) {
    try {
      const res = await request.get('/api/templates');
      allTemplates.value = res.data || res;
    } catch (e) {}
  }
};

const filteredTemplates = computed(() => {
  if (activeCategory.value === 'all') return allTemplates.value;
  return allTemplates.value.filter(t => t.category === activeCategory.value);
});

const applyAiTemplate = (item) => {
  userQuery.value = item.prompt_text;
  templateVisible.value = false;
  message.success(`已应用模板：${item.title}`);
};

const getCategoryColor = (cat) => {
  if (cat === '计算') return 'cyan';
  if (cat === '清洗') return 'orange';
  if (cat === '统计') return 'purple';
  return 'blue';
};
</script>

<style scoped>
/* ================== 全局布局 ================== */
.dashboard-container { height: 100%; display: flex; flex-direction: column; padding: 0 20px; }
.status-bar { display: flex; justify-content: space-between; align-items: center; padding-top: 10px; }
.file-selector { display: inline-flex; align-items: center; font-size: 14px; }
.ml-2 { margin-left: 8px; }
.ml-3 { margin-left: 16px; }
.mr-2 { margin-right: 8px; }
.workspace { display: flex; flex: 1; gap: 20px; height: 0; padding-bottom: 20px; }
.data-panel { flex: 6; display: flex; flex-direction: column; border: 1px solid #f0f0f0; border-radius: 8px; overflow: hidden; background: #fff; }
.panel-header { padding: 12px 16px; background: #fafafa; border-bottom: 1px solid #f0f0f0; font-weight: 600; display: flex; justify-content: space-between; align-items: center;}
.table-wrapper { flex: 1; overflow: hidden; position: relative; }

/* ================== AI 面板布局 ================== */
.ai-panel { flex: 4; display: flex; flex-direction: column; border: 1px solid #e6f7ff; border-radius: 8px; background: #f0f9ff; transition: all 0.3s; }
.ai-header { padding: 8px 16px; background: #e6f7ff; border-bottom: 1px solid #bae7ff; }

/* 聊天/操作 窗口通用容器 */
.chat-window { flex: 1; padding: 20px; overflow-y: auto; scroll-behavior: smooth; position: relative; }
.mode-container { height: 100%; }

/* 欢迎页通用 */
.welcome-box { text-align: center; color: #666; margin-top: 40px; animation: fadeIn 0.5s; }
.welcome-box .sub-text { font-size: 12px; color: #999; margin-top: 5px; }
.icon-bg { font-size: 40px; color: #faad14; background: #fffbe6; width: 80px; height: 80px; line-height: 80px; border-radius: 50%; margin: 0 auto 15px; }
.icon-bg.blue { color: #1890ff; background: #e6f7ff; }
.suggestion-chips { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; margin-top: 15px; cursor: pointer;}

/* ================== 操作结果卡片 (新版) ================== */
.result-card { background: #fff; padding: 16px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); border: 1px solid #e6f7ff; }
.result-title { font-weight: bold; margin-bottom: 12px; font-size: 16px; display: flex; align-items: center; gap: 8px; color: #1890ff;}

/* 🔥 Excel 公式高亮样式 (淡黄色背景) 🔥 */
.formula-highlight {
  background: #fffbe6; /* 淡黄色 */
  border: 1px solid #ffe58f; /* 深黄色边框 */
  padding: 12px 16px;
  border-radius: 6px;
  margin-bottom: 15px;
  box-shadow: 0 2px 6px rgba(0,0,0,0.02);
}

.code-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  border-bottom: 1px dashed #ffe58f;
  padding-bottom: 6px;
}

.code-header .label-text {
  font-weight: bold;
  color: #faad14; /* 黄色标题 */
  font-size: 14px;
}

.code-content {
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 16px; /* 字号放大 */
  font-weight: 500;
  color: #333;
  word-break: break-all;
  line-height: 1.6;
}

.analysis-text { font-size: 14px; color: #555; margin-top: 12px; border-top: 1px dashed #eee; padding-top: 10px;}

/* ================== Chat 模式样式 ================== */
.chat-list { display: flex; flex-direction: column; gap: 16px; padding-bottom: 10px; }
.chat-bubble { display: flex; gap: 10px; max-width: 90%; }
.chat-bubble.user { align-self: flex-end; flex-direction: row-reverse; }
.chat-bubble.ai { align-self: flex-start; }

.bubble-content { background: #fff; padding: 10px 14px; border-radius: 8px; font-size: 14px; color: #333; box-shadow: 0 2px 5px rgba(0,0,0,0.05); position: relative; border: 1px solid #f0f0f0;}
.chat-bubble.user .bubble-content { background: #1890ff; color: #fff; border: none; }
.chat-bubble.ai .bubble-content { background: #fff; border-top-left-radius: 2px; }
.chat-bubble.user .bubble-content { border-top-right-radius: 2px; }

.typing-indicator span { display: inline-block; width: 6px; height: 6px; background-color: #ccc; border-radius: 50%; margin: 0 2px; animation: bounce 1.4s infinite ease-in-out both; }
.typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
.typing-indicator span:nth-child(2) { animation-delay: -0.16s; }
@keyframes bounce { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); } }

/* ================== 底部输入区 ================== */
.input-area { padding: 15px; background: #fff; border-top: 1px solid #e6f7ff; border-radius: 0 0 8px 8px;}
.action-bar { display: flex; align-items: center; justify-content: space-between; margin-top: 10px; }
.chat-btn { width: 120px; transition: all 0.3s; }

/* ================== 弹窗及列表样式 ================== */
.library-container { height: 100%; display: flex; flex-direction: column; }
.scroll-area { overflow-y: auto; flex: 1; padding: 20px 0; }
.excel-mode-container { height: 100%; overflow: hidden; }
.func-list-scroll { height: 100%; overflow-y: auto; padding: 0 16px; }

.template-card { cursor: pointer; transition: all 0.3s; border-color: #eee; }
.template-card:hover { border-color: #1890ff; transform: translateY(-2px); }
.template-desc { color: #888; font-size: 12px; height: 40px; overflow: hidden; margin-bottom: 10px; }
.template-footer { display: flex; justify-content: space-between; align-items: center; }
.use-btn { font-size: 12px; color: #1890ff; display: none; }
.template-card:hover .use-btn { display: inline-block; }

/* 原生函数列表样式 */
.func-item-header { display: flex; align-items: center; margin-bottom: 4px; gap: 10px; }
.func-desc { font-size: 13px; color: #666; }
.syntax-box {
  background: #f7f7f7; padding: 6px 10px; border-radius: 4px;
  display: flex; justify-content: space-between; align-items: center;
  cursor: pointer; border: 1px solid #eee; transition: all 0.2s;
}
.syntax-box:hover { border-color: #1890ff; background: #e6f7ff; }
.syntax-box code { font-family: monospace; color: #d63384; font-size: 12px; }
.copy-icon { color: #999; font-size: 12px; }

/* 动画 */
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
.slide-up-enter-active { transition: all 0.4s ease; }
.slide-up-enter-from { opacity: 0; transform: translateY(20px); }
</style>