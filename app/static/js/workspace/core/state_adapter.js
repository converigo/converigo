/**
 * StateAdapter
 *
 * Isolated adapter layer between the Flow Controller and the existing runtime UI state.
 * This module delegates state operations to `window.ConverigoStateController` and
 * does not create or own any runtime state itself.
 */

class StateAdapter {
  constructor(options = {}) {
    this.stateSource = options.stateSource || window.ConverigoStateController;
    this.stateEnum = options.stateEnum || window.ConverigoUIState;
    this.debugPrefix = '[StateAdapter]';
  }

  getState() {
    if (!this.stateSource || typeof this.stateSource.getState !== 'function') {
      return null;
    }

    return this.stateSource.getState();
  }

  setState(nextState) {
    if (!this.stateSource || typeof this.stateSource.setState !== 'function') {
      return false;
    }

    if (this.stateEnum && !Object.values(this.stateEnum).includes(nextState)) {
      return false;
    }

    this.stateSource.setState(nextState);
    return true;
  }

  hasState(state) {
    const currentState = this.getState();
    return currentState === state;
  }

  reset() {
    if (!this.stateEnum || !this.stateEnum.LANDING) {
      return false;
    }

    return this.setState(this.stateEnum.LANDING);
  }
}

window.StateAdapter = StateAdapter;
