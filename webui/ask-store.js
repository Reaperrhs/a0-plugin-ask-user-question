import { createStore } from '/js/AlpineStore.js';
import { callJsonApi } from '/js/api.js';
import {
  toastFrontendSuccess,
  toastFrontendError,
} from '/components/notifications/notification-store.js';

export const store = createStore('askUserQuestion', {
  showModal: false,
  session: null,
  sessionId: '',
  questions: [],
  activeTab: 0,
  answers: {},
  otherTexts: {},
  notes: {},
  submitting: false,
  pollTimer: null,

  get totalQuestions() {
    return this.questions.length;
  },

  get showSubmitTab() {
    return this.activeTab === this.questions.length;
  },

  get allAnswered() {
    for (let i = 0; i < this.questions.length; i++) {
      const ans = this.answers[i];
      if (!ans || ans.length === 0) {
        if (!this.otherTexts[i] || !this.otherTexts[i].trim()) {
          return false;
        }
      }
    }
    return true;
  },

_startPolling() {
    if (this.pollTimer) clearInterval(this.pollTimer);
    this.pollTimer = setInterval(() => this._poll(), 2000);
  },

  async _poll() {
    try {
      const ctxid = globalThis.getContext?.();
      if (!ctxid) return;

      if (this.showModal && this.session) return;

      const res = await callJsonApi(
        '/plugins/ask_user_question/get_pending',
        { context_id: ctxid }
      );

      if (res?.ok && res.pending) {
        this.sessionId = res.session_id;
        this.questions = res.questions;
        this.answers = {};
        this.otherTexts = {};
        this.notes = {};
        this.activeTab = 0;
        this.submitting = false;
        this.session = res;
        this.showModal = true;
      }
    } catch (e) {
      // silent
    }
  },

  setTab(index) {
    this.activeTab = index;
  },

  nextTab() {
    if (this.activeTab < this.questions.length) {
      this.activeTab++;
    }
  },

  prevTab() {
    if (this.activeTab > 0) {
      this.activeTab--;
    }
  },

  toggleOption(qIndex, label) {
    if (!this.answers[qIndex]) this.answers[qIndex] = [];
    const q = this.questions[qIndex];
    const arr = this.answers[qIndex];

    if (q.multiSelect) {
      const idx = arr.indexOf(label);
      if (idx >= 0) {
        arr.splice(idx, 1);
      } else {
        arr.push(label);
      }
    } else {
      if (label === '__other__') {
        this.answers[qIndex] = ['__other__'];
      } else {
        this.answers[qIndex] = [label];
      }
    }
  },

  isSelected(qIndex, label) {
    const arr = this.answers[qIndex] || [];
    return arr.includes(label);
  },

  getSelectedLabels(qIndex) {
    const arr = this.answers[qIndex] || [];
    const q = this.questions[qIndex];
    return arr
      .filter((l) => l !== '__other__')
      .map((l) => {
        const opt = q.options.find((o) => o.label === l);
        return opt ? opt.label : l;
      });
  },

  getAnswerSummary(qIndex) {
    const labels = this.getSelectedLabels(qIndex);
    const other = this.otherTexts[qIndex] || '';
    const parts = [...labels];
    if (other.trim()) parts.push('Other: ' + other.trim());
    return parts.join(', ') || 'Not answered';
  },

  getPreviewContent(qIndex) {
    const arr = this.answers[qIndex] || [];
    const q = this.questions[qIndex];
    for (const label of arr) {
      const opt = q.options.find((o) => o.label === label);
      if (opt && opt.preview) return opt.preview;
    }
    return '';
  },

  async submit() {
    if (!this.allAnswered) {
      toastFrontendError('Please answer all questions before submitting.');
      return;
    }

    this.submitting = true;
    try {
      const answersPayload = this.questions.map((q, i) => ({
        question_index: i,
        selected: this.getSelectedLabels(i),
        other_text: (this.otherTexts[i] || '').trim(),
        notes: (this.notes[i] || '').trim(),
      }));

      const res = await callJsonApi(
        '/plugins/ask_user_question/submit_answer',
        {
          session_id: this.sessionId,
          answers: answersPayload,
          cancelled: false,
        }
      );

      if (res?.ok) {
        toastFrontendSuccess('Answers submitted!');
        this._closeModal();
      } else {
        toastFrontendError(res?.error || 'Failed to submit answers.');
      }
    } catch (e) {
      toastFrontendError(e.message || 'Error submitting answers.');
    } finally {
      this.submitting = false;
    }
  },

  async cancel() {
    this.submitting = true;
    try {
      await callJsonApi('/plugins/ask_user_question/submit_answer', {
        session_id: this.sessionId,
        answers: [],
        cancelled: true,
      });
      this._closeModal();
    } catch (e) {
      this._closeModal();
    } finally {
      this.submitting = false;
    }
  },

  _closeModal() {
    this.showModal = false;
    this.session = null;
    this.sessionId = '';
    this.questions = [];
    this.answers = {};
    this.otherTexts = {};
    this.notes = {};
    this.activeTab = 0;
  },
});
