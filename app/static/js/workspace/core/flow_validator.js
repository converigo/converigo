/**
 * FlowValidator
 *
 * Core stabilization layer for validating transitions before the Flow Controller assumes runtime ownership.
 * This module is intentionally isolated and does not interact with DOM, events, UI, or conversion/download logic.
 */

class FlowValidator {
  constructor() {
    this.states = [
      'LANDING',
      'WORKSPACE',
      'CONVERTING',
      'PREPARING_DOWNLOAD',
      'DOWNLOAD_READY',
      'DOWNLOADING',
      'FINISHED',
      'ERROR',
    ];

    this.transitions = {
      LANDING: ['WORKSPACE', 'ERROR'],
      WORKSPACE: ['CONVERTING', 'ERROR'],
      CONVERTING: ['PREPARING_DOWNLOAD', 'ERROR'],
      PREPARING_DOWNLOAD: ['DOWNLOAD_READY', 'ERROR'],
      DOWNLOAD_READY: ['DOWNLOADING', 'ERROR'],
      DOWNLOADING: ['FINISHED', 'ERROR'],
      FINISHED: ['WORKSPACE', 'ERROR'],
      ERROR: ['LANDING', 'WORKSPACE'],
    };
  }

  validate(currentState, nextState) {
    const result = {
      currentState: currentState || null,
      nextState: nextState || null,
      allowed: false,
      reason: '',
    };

    if (!currentState || !nextState) {
      result.reason = 'Both currentState and nextState must be provided.';
      return result;
    }

    if (!this.states.includes(currentState)) {
      result.reason = `Unknown current state: ${currentState}`;
      return result;
    }

    if (!this.states.includes(nextState)) {
      result.reason = `Unknown next state: ${nextState}`;
      return result;
    }

    const allowedTransitions = this.getAllowedTransitions(currentState);
    const allowed = allowedTransitions.includes(nextState);

    result.allowed = allowed;
    result.reason = allowed
      ? `Transition ${currentState} → ${nextState} is allowed.`
      : `Transition ${currentState} → ${nextState} is not allowed.`;

    return result;
  }

  isAllowed(currentState, nextState) {
    const validation = this.validate(currentState, nextState);
    return validation.allowed;
  }

  getAllowedTransitions(state) {
    if (!state || !this.states.includes(state)) {
      return [];
    }
    return this.transitions[state] || [];
  }
}

window.FlowValidator = FlowValidator;
