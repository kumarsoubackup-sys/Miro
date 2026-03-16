import service from './index.js';

/**
 * Analyze a topic and get suggested research categories.
 * @param {String} prompt - The simulation topic/requirement
 * @returns {Promise}
 */
export const analyzeTopicAPI = (prompt) => {
  return service.post('/api/seed/analyze', { prompt });
};

/**
 * Start seed data generation.
 * @param {String} prompt - The simulation topic/requirement
 * @param {Array} categories - Selected research categories
 * @param {String} depth - 'quick' or 'thorough'
 * @returns {Promise}
 */
export const generateSeedAPI = (prompt, categories, depth) => {
  return service.post('/api/seed/generate', { prompt, categories, depth });
};

/**
 * Poll seed generation progress.
 * @param {String} taskId - Task ID from generateSeedAPI
 * @returns {Promise}
 */
export const getSeedTaskAPI = (taskId) => {
  return service.get(`/api/seed/task/${taskId}`);
};

/**
 * Get content of a generated seed file.
 * @param {String} taskId - Task ID
 * @param {String} filename - Filename of the seed file
 * @returns {Promise}
 */
export const getSeedFileAPI = (taskId, filename) => {
  return service.get(`/api/seed/file/${taskId}/${filename}`);
};
