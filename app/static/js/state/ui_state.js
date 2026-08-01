/**
 * Converigo centralized UI state definitions
 * Sprint 2: state foundation only.
 */

window.ConverigoUIState = {
    LANDING: 'LANDING',
    WORKSPACE: 'WORKSPACE',
    CONVERTING: 'CONVERTING',
    PREPARING_DOWNLOAD: 'PREPARING_DOWNLOAD',
    DOWNLOAD_READY: 'DOWNLOAD_READY',
    DOWNLOADING: 'DOWNLOADING',
    FINISHED: 'FINISHED',
    ERROR: 'ERROR',
};

window.ConverigoStateController = {
    currentState: window.ConverigoUIState.LANDING,
    setState(state) {
        if (!Object.values(window.ConverigoUIState).includes(state)) {
            console.warn('Invalid UI state:', state);
            return;
        }
        this.currentState = state;
        window.dispatchEvent(new CustomEvent('ui-state-changed', { detail: { state } }));
    },
    getState() {
        return this.currentState;
    },
};
