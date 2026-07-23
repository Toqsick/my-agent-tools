/**
 * Plugin-Template mit V7.2 Health-Score-Pattern.
 *
 * V7.2 erweitert invoke() um Telemetry:
 * - usage_score boost +0.01 on success (cap 1.0)
 * - usage_score decay -0.05 on error (floor 0.0)
 * - invoke_count / error_count tracking
 * - last_invoked_at timestamp
 *
 * Verwendung:
 *   const plugin = require('./index.js');
 *   const result = await plugin.invoke(input);
 *   // Health-Score wird automatisch aktualisiert
 */

module.exports = {
  manifest: require('./plugin.json'),

  async invoke(input) {
    // 1) Input-Validation
    if (!input || !input.action) {
      throw new Error('[PLUGIN_NAME] missing required input: action');
    }

    // 2) Action-Dispatch
    try {
      let result;
      switch (input.action) {
        case 'ping':
          result = { ok: true, who: 'PLUGIN_NAME', ts: Date.now() };
          break;
        default:
          throw new Error(`[PLUGIN_NAME] unknown action: ${input.action}`);
      }
      return result;
    } catch (err) {
      // Errors propagieren — Registry dekrementiert usage_score automatisch
      throw err;
    }
  },

  async shutdown() {
    // Optional: cleanup resources (HTTP clients, DB connections, etc.)
  },
};