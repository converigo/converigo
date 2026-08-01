/**
 * Flow Controller Framework
 *
 * This file defines the FlowController foundation only.
 * It is intentionally isolated and does not alter current runtime behavior.
 */

class FlowController {
  constructor(options = {}) {
    this.stateSource = options.stateSource || window.ConverigoStateController;
    this.eventSource = options.eventSource || window.ConverigoEvents;
    this.featureFlag = window.__ENABLE_DOWNLOAD_V2__ === true;
    this.initialized = false;
    this.listeners = new Map();
    this.debugPrefix = '[FlowController]';

    this.validator = options.validator || (typeof FlowValidator !== 'undefined' ? new FlowValidator() : null);
    this.stateAdapter = options.stateAdapter || (typeof StateAdapter !== 'undefined' ? new StateAdapter() : null);

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

  initialize() {
    if (this.initialized) {
      return;
    }

    this.initialized = true;

    if (!this.featureFlag) {
      this._debug('Feature flag disabled; controller is passive. No runtime ownership will be claimed.');
      return;
    }

    this._debug('Feature flag enabled; controller is ready in passive framework mode.');
  }

  destroy() {
    this.listeners.clear();
    this.initialized = false;
    this._debug('Destroyed; event registrations removed.');
  }

  getCurrentState() {
    if (this.stateAdapter && typeof this.stateAdapter.getState === 'function') {
      return this.stateAdapter.getState();
    }

    if (!this.stateSource || typeof this.stateSource.getState !== 'function') {
      return null;
    }

    return this.stateSource.getState();
  }

  canTransition(nextState) {
    const currentState = this.getCurrentState();
    if (!currentState || !this.states.includes(nextState)) {
      return false;
    }

    const allowed = this.transitions[currentState] || [];
    return allowed.includes(nextState);
  }

  transition(nextState) {
    if (!this.initialized) {
      this._debug('Cannot transition before initialize() is called.');
      return {
        currentState: this.getCurrentState(),
        nextState,
        allowed: false,
        reason: 'FlowController must be initialized before transitions are processed.',
      };
    }

    const currentState = this.getCurrentState();
    const validation = this.validator
      ? this.validator.validate(currentState, nextState)
      : {
          currentState,
          nextState,
          allowed: false,
          reason: 'FlowValidator is unavailable.',
        };

    if (!validation.allowed) {
      this._debug(`Transition blocked: ${currentState} → ${nextState}. Reason: ${validation.reason}`);
      return validation;
    }

    const requestedStateUpdate =
      this.stateAdapter && typeof this.stateAdapter.setState === 'function'
        ? this.stateAdapter.setState(nextState)
        : false;

    if (this.featureFlag) {
      this._debug(`Validated transition: ${currentState} → ${nextState}. Legacy flow remains authoritative.`);
    } else {
      this._debug(`Passive transition validated: ${currentState} → ${nextState}. No runtime ownership claimed.`);
    }

    return {
      ...validation,
      requestedStateUpdate,
    };
  }

  register(eventName, callback) {
    if (typeof callback !== 'function' || !eventName) {
      return false;
    }

    if (!this.listeners.has(eventName)) {
      this.listeners.set(eventName, new Set());
    }

    this.listeners.get(eventName).add(callback);
    return true;
  }

  unregister(eventName, callback) {
    if (!this.listeners.has(eventName)) {
      return false;
    }

    const callbacks = this.listeners.get(eventName);
    callbacks.delete(callback);

    if (callbacks.size === 0) {
      this.listeners.delete(eventName);
    }

    return true;
  }

  _debug(message) {
    if (typeof console !== 'undefined' && typeof console.debug === 'function') {
      console.debug(`${this.debugPrefix} ${message}`);
    }
  }
}

window.FlowController = FlowController;
