<template>
  <Teleport to="body">
    <div v-if="show" class="seed-overlay" @click.self="handleClose">
      <div class="seed-modal">
        <!-- Header -->
        <div class="modal-header">
          <div class="header-left">
            <span class="header-icon">&#9670;</span>
            <span class="header-title">AI Research Assistant</span>
          </div>
          <button class="close-btn" @click="handleClose">&times;</button>
        </div>

        <!-- Phase 1: Category Selection -->
        <div v-if="phase === 'select'" class="modal-body">
          <p class="modal-desc">
            ARUS will research your topic using live web data and generate comprehensive seed files.
          </p>

          <div class="section-label">RESEARCH CATEGORIES</div>
          <div class="category-list">
            <label
              v-for="cat in categories"
              :key="cat.id"
              class="category-item"
            >
              <input
                type="checkbox"
                :value="cat.id"
                v-model="selectedIds"
                class="cat-checkbox"
              />
              <div class="cat-info">
                <span class="cat-name">{{ cat.name }}</span>
                <span class="cat-desc">{{ cat.description }}</span>
              </div>
            </label>
          </div>

          <div class="section-label depth-label">RESEARCH DEPTH</div>
          <div class="depth-toggle">
            <button
              class="depth-btn"
              :class="{ active: depth === 'quick' }"
              @click="depth = 'quick'"
            >
              <span class="depth-name">Quick</span>
              <span class="depth-desc">Broader web search, concise reports (~1 min)</span>
            </button>
            <button
              class="depth-btn"
              :class="{ active: depth === 'thorough' }"
              @click="depth = 'thorough'"
            >
              <span class="depth-name">Thorough</span>
              <span class="depth-desc">Exhaustive research, hundreds of sources (~3 min)</span>
            </button>
          </div>

          <div class="modal-actions">
            <button class="btn-cancel" @click="handleClose">Cancel</button>
            <button
              class="btn-primary"
              :disabled="selectedIds.length === 0"
              @click="startGeneration"
            >
              Start Research
              <span class="btn-arrow">&rarr;</span>
            </button>
          </div>
        </div>

        <!-- Phase 2: Progress -->
        <div v-else-if="phase === 'progress'" class="modal-body">
          <div class="progress-container">
            <div class="progress-bar-track">
              <div
                class="progress-bar-fill"
                :style="{ width: seedTaskState.progress + '%' }"
              ></div>
            </div>
            <div class="progress-text">{{ seedTaskState.progress }}%</div>
          </div>

          <div v-if="seedTaskState.currentFile" class="current-file">
            <span class="spinner"></span>
            Researching {{ seedTaskState.currentFile }}...
          </div>

          <div class="completed-list" v-if="seedTaskState.completedFiles.length > 0">
            <div class="section-label">COMPLETED</div>
            <div
              v-for="file in seedTaskState.completedFiles"
              :key="file.name"
              class="completed-item"
            >
              <span class="check-icon">&#10003;</span>
              <span class="completed-name">{{ file.display_name }}</span>
            </div>
          </div>

          <div v-if="seedTaskState.error" class="error-message">
            Research generation failed: {{ seedTaskState.error }}
          </div>
        </div>

        <!-- Phase 3: Complete -->
        <div v-else-if="phase === 'complete'" class="modal-body">
          <div class="complete-banner">
            <span class="complete-icon">&#10003;</span>
            Research complete!
          </div>

          <div class="section-label">GENERATED FILES</div>
          <div class="file-list">
            <div
              v-for="file in seedTaskState.completedFiles"
              :key="file.name"
              class="file-item"
            >
              <span class="file-name">{{ file.display_name }}</span>
              <button class="btn-preview" @click="previewFile(file)">
                Preview
              </button>
            </div>
          </div>

          <div class="modal-actions">
            <button class="btn-cancel" @click="handleClose">Cancel</button>
            <button class="btn-primary" @click="confirmFiles">
              Use These Files
              <span class="btn-arrow">&rarr;</span>
            </button>
          </div>
        </div>

        <!-- Preview Overlay -->
        <div v-if="previewContent !== null" class="preview-overlay">
          <div class="preview-header">
            <span class="preview-title">{{ previewTitle }}</span>
            <button class="close-btn" @click="previewContent = null">&times;</button>
          </div>
          <div class="preview-body">
            <pre class="preview-text">{{ previewContent }}</pre>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue';
import { generateSeedAPI, getSeedTaskAPI, getSeedFileAPI } from '../api/seed.js';
import {
  seedTaskState,
  startSeedTask,
  updateSeedProgress,
  resetSeedTask,
} from '../store/seedTask.js';

const props = defineProps({
  prompt: { type: String, default: '' },
  show: { type: Boolean, default: false },
  categories: { type: Array, default: () => [] },
});

const emit = defineEmits(['files-ready', 'close']);

// UI-only local state (selection phase)
const selectedIds = ref([]);
const depth = ref('quick');

// Preview state
const previewContent = ref(null);
const previewTitle = ref('');

// Module-level poll timer — persists across modal open/close cycles
let pollTimer = null;

// Phase is derived from store status
const phase = computed(() => {
  const status = seedTaskState.status;
  if (status === 'completed') return 'complete';
  if (status === 'generating' || status === 'analyzing') return 'progress';
  if (status === 'failed') return 'progress'; // show error inside progress view
  return 'select';
});

// Pre-check recommended categories when categories prop changes
watch(
  () => props.categories,
  (cats) => {
    if (cats && cats.length > 0) {
      selectedIds.value = cats
        .filter((c) => c.recommended)
        .map((c) => c.id);
    }
  },
  { immediate: true }
);

// When modal opens: reset preview, re-apply selections if idle.
// When modal closes: do NOT stop polling — let it continue in the background.
watch(
  () => props.show,
  (isVisible) => {
    if (isVisible) {
      previewContent.value = null;
      previewTitle.value = '';
      // Only reset selections when there is no active task
      if (seedTaskState.status === 'idle') {
        if (props.categories && props.categories.length > 0) {
          selectedIds.value = props.categories
            .filter((c) => c.recommended)
            .map((c) => c.id);
        }
      }
      // If an active task exists and we're not already polling, resume
      if (seedTaskState.active && !pollTimer) {
        startPolling();
      }
    }
    // Intentionally not stopping polling on close
  }
);

// On mount: resume polling if the store already has an active task
onMounted(() => {
  if (seedTaskState.active && !pollTimer) {
    startPolling();
  }
});

const handleClose = () => {
  // Do NOT stop polling — background task continues
  emit('close');
};

const startGeneration = async () => {
  const selectedCategories = props.categories.filter((c) =>
    selectedIds.value.includes(c.id)
  );

  if (selectedCategories.length === 0) return;

  // Reset store so template immediately shows progress phase
  resetSeedTask();

  try {
    const res = await generateSeedAPI(
      props.prompt,
      selectedCategories,
      depth.value
    );
    startSeedTask(res.task_id, props.prompt, selectedCategories, depth.value);
    startPolling();
  } catch (err) {
    // Surface the error in the store so the template can show it
    updateSeedProgress({
      status: 'failed',
      progress: 0,
      current_file: '',
      completed_files: [],
      error: err.message || 'Failed to start generation',
    });
  }
};

const startPolling = () => {
  stopPolling();
  pollTimer = setInterval(pollTask, 2000);
};

const stopPolling = () => {
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
};

const pollTask = async () => {
  if (!seedTaskState.taskId) return;

  try {
    const res = await getSeedTaskAPI(seedTaskState.taskId);
    updateSeedProgress(res);

    if (res.status === 'completed' || res.status === 'failed') {
      stopPolling();
    }
  } catch (err) {
    stopPolling();
    updateSeedProgress({
      status: 'failed',
      progress: seedTaskState.progress,
      current_file: '',
      completed_files: seedTaskState.completedFiles,
      error: err.message || 'Failed to poll task status',
    });
  }
};

const previewFile = async (file) => {
  try {
    const res = await getSeedFileAPI(seedTaskState.taskId, file.name);
    previewContent.value = res.content;
    previewTitle.value = file.display_name;
  } catch (err) {
    previewContent.value = 'Failed to load file content: ' + err.message;
    previewTitle.value = file.display_name;
  }
};

const confirmFiles = () => {
  const files = seedTaskState.completedFiles.map((f) => ({
    name: f.name,
    displayName: f.display_name,
    taskId: seedTaskState.taskId,
    filename: f.name,
  }));
  emit('files-ready', files);
};
</script>

<style scoped>
.seed-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: fadeIn 0.2s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.seed-modal {
  background: #FFFFFF;
  border: 1px solid #E5E5E5;
  width: 560px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  position: relative;
  animation: slideUp 0.25s ease-out;
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #E5E5E5;
  background: #FAFAFA;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-icon {
  color: #FF4500;
  font-size: 10px;
}

.header-title {
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.5px;
}

.close-btn {
  background: none;
  border: none;
  font-size: 20px;
  color: #999;
  cursor: pointer;
  line-height: 1;
  padding: 0 4px;
}

.close-btn:hover {
  color: #333;
}

.modal-body {
  padding: 20px;
  overflow-y: auto;
  flex: 1;
}

.modal-desc {
  font-size: 13px;
  color: #666;
  line-height: 1.6;
  margin-bottom: 20px;
}

.section-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  font-weight: 600;
  color: #AAA;
  letter-spacing: 0.5px;
  margin-bottom: 10px;
}

.depth-label {
  margin-top: 20px;
}

/* Category list */
.category-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.category-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 12px;
  border: 1px solid #EAEAEA;
  cursor: pointer;
  transition: border-color 0.2s;
}

.category-item:hover {
  border-color: #CCC;
}

.cat-checkbox {
  margin-top: 2px;
  accent-color: #000;
  cursor: pointer;
}

.cat-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.cat-name {
  font-size: 13px;
  font-weight: 600;
  color: #000;
}

.cat-desc {
  font-size: 11px;
  color: #888;
  line-height: 1.4;
}

/* Depth toggle */
.depth-toggle {
  display: flex;
  gap: 10px;
}

.depth-btn {
  flex: 1;
  padding: 12px;
  border: 1px solid #EAEAEA;
  background: #FAFAFA;
  cursor: pointer;
  text-align: left;
  display: flex;
  flex-direction: column;
  gap: 4px;
  transition: all 0.2s;
}

.depth-btn:hover {
  border-color: #CCC;
}

.depth-btn.active {
  border-color: #000;
  background: #FFF;
}

.depth-name {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  font-weight: 700;
  color: #000;
}

.depth-desc {
  font-size: 10px;
  color: #999;
  line-height: 1.3;
}

/* Modal actions */
.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #EAEAEA;
}

.btn-cancel {
  padding: 10px 20px;
  background: none;
  border: 1px solid #DDD;
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  font-weight: 600;
  color: #666;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-cancel:hover {
  border-color: #999;
  color: #333;
}

.btn-primary {
  padding: 10px 20px;
  background: #000;
  border: none;
  color: #FFF;
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s;
}

.btn-primary:hover:not(:disabled) {
  background: #FF4500;
}

.btn-primary:disabled {
  background: #CCC;
  cursor: not-allowed;
}

.btn-arrow {
  font-size: 14px;
}

/* Progress phase */
.progress-container {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.progress-bar-track {
  flex: 1;
  height: 6px;
  background: #EAEAEA;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  background: #000;
  transition: width 0.5s ease;
}

.progress-text {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  font-weight: 700;
  color: #000;
  min-width: 36px;
  text-align: right;
}

.current-file {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
  color: #FF4500;
  margin-bottom: 20px;
  font-family: 'JetBrains Mono', monospace;
}

.spinner {
  width: 14px;
  height: 14px;
  border: 2px solid #FFCCBC;
  border-top-color: #FF4500;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  flex-shrink: 0;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.completed-list {
  margin-top: 16px;
}

.completed-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 0;
  border-bottom: 1px solid #F5F5F5;
  font-size: 12px;
}

.check-icon {
  color: #2E7D32;
  font-weight: 700;
  font-size: 13px;
}

.completed-name {
  color: #333;
}

.error-message {
  margin-top: 16px;
  padding: 12px;
  background: #FFF5F5;
  border: 1px solid #FFCDD2;
  color: #C62828;
  font-size: 12px;
  font-family: 'JetBrains Mono', monospace;
}

/* Complete phase */
.complete-banner {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  background: #E8F5E9;
  border: 1px solid #C8E6C9;
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px;
  font-weight: 700;
  color: #2E7D32;
  margin-bottom: 20px;
}

.complete-icon {
  font-size: 16px;
}

.file-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.file-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  border: 1px solid #EAEAEA;
}

.file-name {
  font-size: 12px;
  font-weight: 600;
  color: #333;
}

.btn-preview {
  padding: 4px 10px;
  background: none;
  border: 1px solid #DDD;
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  font-weight: 600;
  color: #666;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-preview:hover {
  border-color: #999;
  color: #000;
}

/* Preview overlay */
.preview-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: #FFFFFF;
  display: flex;
  flex-direction: column;
  z-index: 10;
  animation: fadeIn 0.15s ease-out;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #E5E5E5;
  background: #FAFAFA;
  flex-shrink: 0;
}

.preview-title {
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px;
  font-weight: 700;
}

.preview-body {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.preview-text {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  line-height: 1.6;
  color: #333;
  white-space: pre-wrap;
  word-wrap: break-word;
  margin: 0;
}
</style>
