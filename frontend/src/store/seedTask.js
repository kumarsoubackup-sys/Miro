import { reactive } from 'vue';

const state = reactive({
  active: false,
  taskId: null,
  prompt: '',
  categories: [],
  depth: 'quick',
  status: 'idle', // idle | analyzing | generating | completed | failed
  progress: 0,
  currentFile: '',
  completedFiles: [],
  error: null,
});

export function startSeedTask(taskId, prompt, categories, depth) {
  state.active = true;
  state.taskId = taskId;
  state.prompt = prompt;
  state.categories = categories;
  state.depth = depth;
  state.status = 'generating';
  state.progress = 0;
  state.currentFile = '';
  state.completedFiles = [];
  state.error = null;
}

export function updateSeedProgress(data) {
  state.status = data.status;
  state.progress = data.progress;
  state.currentFile = data.current_file || '';
  state.completedFiles = data.completed_files || [];
  if (data.error) state.error = data.error;
  if (data.status === 'completed' || data.status === 'failed') {
    state.active = data.status !== 'failed';
  }
}

export function resetSeedTask() {
  state.active = false;
  state.taskId = null;
  state.status = 'idle';
  state.progress = 0;
  state.currentFile = '';
  state.completedFiles = [];
  state.error = null;
}

export { state as seedTaskState };
