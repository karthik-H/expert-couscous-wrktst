import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import MockAdapter from 'axios-mock-adapter';
import { jest } from '@jest/globals';

// Import the api instance
import api from '../../../frontend/src/api/client';

describe('frontend_api_client', () => {
  const TOKEN_KEY = 'token'; // Adjust if your implementation uses a different key

  let mock: MockAdapter;
  let originalLocalStorage: Storage | undefined;
  let localStorageMock: any;

  beforeEach(() => {
    // Setup axios mock adapter
    mock = new MockAdapter(api);
    mock.onAny().reply(200, { success: true });

    // Save original localStorage
    originalLocalStorage = global.localStorage;

    // Setup localStorage mock
    let store: Record<string, any> = {};
    localStorageMock = {
      getItem: jest.fn((key: string) => store[key] ?? null),
      setItem: jest.fn((key: string, value: string) => { store[key] = value; }),
      removeItem: jest.fn((key: string) => { delete store[key]; }),
      clear: jest.fn(() => { store = {}; }),
    };
    Object.defineProperty(global, 'localStorage', {
      value: localStorageMock,
      configurable: true,
      writable: true,
    });
    localStorageMock.clear();
    jest.clearAllMocks();
  });

  afterEach(() => {
    // Restore original localStorage
    if (originalLocalStorage) {
      Object.defineProperty(global, 'localStorage', {
        value: originalLocalStorage,
        configurable: true,
        writable: true,
      });
    } else {
      // Remove localStorage if it didn't exist
      // @ts-ignore
      delete global.localStorage;
    }
    mock.restore();
    jest.resetModules();
  });

  test('adds_authorization_header_when_token_present', async () => {
    const token = 'valid-token-123';
    localStorageMock.setItem(TOKEN_KEY, token);

    let requestHeaders: any = {};
    mock.onGet('/test').reply(config => {
      requestHeaders = config.headers;
      return [200, {}];
    });

    await api.get('/test');

    // Axios merges headers, so check common and Authorization
    const authHeader =
      (requestHeaders && (requestHeaders['Authorization'] || requestHeaders.common?.Authorization));
    expect(authHeader).toBe(`Bearer ${token}`);
  });

  test('does_not_add_authorization_header_when_no_token', async () => {
    localStorageMock.removeItem(TOKEN_KEY);

    let requestHeaders: any = {};
    mock.onGet('/test').reply(config => {
      requestHeaders = config.headers;
      return [200, {}];
    });

    await api.get('/test');

    const authHeader =
      (requestHeaders && (requestHeaders['Authorization'] || requestHeaders.common?.Authorization));
    expect(authHeader).toBeUndefined();
  });

  test('does_not_add_authorization_header_when_token_empty', async () => {
    localStorageMock.setItem(TOKEN_KEY, '');

    let requestHeaders: any = {};
    mock.onGet('/test').reply(config => {
      requestHeaders = config.headers;
      return [200, {}];
    });

    await api.get('/test');

    const authHeader =
      (requestHeaders && (requestHeaders['Authorization'] || requestHeaders.common?.Authorization));
    expect(authHeader).toBeUndefined();
  });

  test('does_not_add_authorization_header_when_token_malformed', async () => {
    // Store a non-string value (simulate by JSON stringifying an object)
    localStorageMock.setItem(TOKEN_KEY, JSON.stringify({ not: 'a string' }));

    let requestHeaders: any = {};
    mock.onGet('/test').reply(config => {
      requestHeaders = config.headers;
      return [200, {}];
    });

    await api.get('/test');

    const authHeader =
      (requestHeaders && (requestHeaders['Authorization'] || requestHeaders.common?.Authorization));
    // Should not add Authorization header if token is not a valid string
    expect(authHeader).toBeUndefined();
  });

  test('uses_configured_base_url', async () => {
    // The baseURL should be set in the api instance
    // We'll check that requests go to the correct URL
    const expectedBaseURL = (api.defaults && api.defaults.baseURL) || '';
    expect(expectedBaseURL).toBeTruthy();

    let requestedUrl = '';
    mock.onGet('/relative-path').reply(config => {
      requestedUrl = config.baseURL
        ? config.baseURL.replace(/\/$/, '') + config.url
        : config.url || '';
      return [200, {}];
    });

    await api.get('/relative-path');
    expect(requestedUrl).toBe(expectedBaseURL.replace(/\/$/, '') + '/relative-path');
  });

  test('handles_interceptor_errors_gracefully', async () => {
    // Simulate localStorage throwing error
    Object.defineProperty(global, 'localStorage', {
      get: () => {
        throw new Error('localStorage inaccessible');
      },
      configurable: true,
    });

    let errorCaught = false;
    let requestHeaders: any = {};
    mock.onGet('/test').reply(config => {
      requestHeaders = config.headers;
      return [200, {}];
    });

    try {
      await api.get('/test');
    } catch (e) {
      errorCaught = true;
    }

    // Should not throw error, request proceeds
    expect(errorCaught).toBe(false);
    const authHeader =
      (requestHeaders && (requestHeaders['Authorization'] || requestHeaders.common?.Authorization));
    expect(authHeader).toBeUndefined();
  });

  test('updates_authorization_header_on_token_change', async () => {
    const token1 = 'token-one';
    const token2 = 'token-two';

    localStorageMock.setItem(TOKEN_KEY, token1);

    let headersFirst: any = {};
    mock.onGet('/first').reply(config => {
      headersFirst = config.headers;
      return [200, {}];
    });

    await api.get('/first');

    localStorageMock.setItem(TOKEN_KEY, token2);

    let headersSecond: any = {};
    mock.onGet('/second').reply(config => {
      headersSecond = config.headers;
      return [200, {}];
    });

    await api.get('/second');

    const authHeaderFirst =
      (headersFirst && (headersFirst['Authorization'] || headersFirst.common?.Authorization));
    const authHeaderSecond =
      (headersSecond && (headersSecond['Authorization'] || headersSecond.common?.Authorization));

    expect(authHeaderFirst).toBe(`Bearer ${token1}`);
    expect(authHeaderSecond).toBe(`Bearer ${token2}`);
  });

  test('handles_missing_localstorage_gracefully', async () => {
    // Remove localStorage from global
    // @ts-ignore
    delete global.localStorage;

    let errorCaught = false;
    let requestHeaders: any = {};
    mock.onGet('/test').reply(config => {
      requestHeaders = config.headers;
      return [200, {}];
    });

    try {
      await api.get('/test');
    } catch (e) {
      errorCaught = true;
    }

    expect(errorCaught).toBe(false);
    const authHeader =
      (requestHeaders && (requestHeaders['Authorization'] || requestHeaders.common?.Authorization));
    expect(authHeader).toBeUndefined();
  });

  test('exports_singleton_api_instance', async () => {
    // Import the api instance again (simulate import in another module)
    const { default: apiAgain } = await import('../../../frontend/src/api/client');
    expect(apiAgain).toBe(api);

    let headersA: any = {};
    let headersB: any = {};

    mock.onGet('/a').reply(config => {
      headersA = config.headers;
      return [200, {}];
    });
    mock.onGet('/b').reply(config => {
      headersB = config.headers;
      return [200, {}];
    });

    localStorageMock.setItem(TOKEN_KEY, 'singleton-token');
    await api.get('/a');
    await apiAgain.get('/b');

    const authHeaderA =
      (headersA && (headersA['Authorization'] || headersA.common?.Authorization));
    const authHeaderB =
      (headersB && (headersB['Authorization'] || headersB.common?.Authorization));

    expect(authHeaderA).toBe('Bearer singleton-token');
    expect(authHeaderB).toBe('Bearer singleton-token');
  });
});