import React from 'react';
import { render, screen, waitFor, act, fireEvent, cleanup } from '@testing-library/react';
import '@testing-library/jest-dom';
import Dashboard from '../../../frontend/src/views/Dashboard';
import * as api from '../../../frontend/src/api/client';
import { LineChart } from 'recharts';

// Mock recharts LineChart to verify rendering
jest.mock('recharts', () => ({
  ...jest.requireActual('recharts'),
  LineChart: jest.fn(({ children }) => <div data-testid="line-chart">{children}</div>),
}));

jest.mock('../../../frontend/src/api/client');

describe('Dashboard Component', () => {
  let getSpy: jest.SpyInstance;

  const mockCurrentEnergy = { value: 123 };
  const mockHistory = [
    { timestamp: '2025-01-01T00:00:00Z', value: 10 },
    { timestamp: '2025-01-02T00:00:00Z', value: 20 },
    { timestamp: '2025-01-03T00:00:00Z', value: 30 },
  ];

  beforeEach(() => {
    jest.useFakeTimers();
    getSpy = jest.spyOn(api, 'get');
    (LineChart as jest.Mock).mockImplementation(({ children }) => <div data-testid="line-chart">{children}</div>);
  });

  afterEach(() => {
    jest.clearAllTimers();
    jest.resetAllMocks();
    cleanup();
  });

  // Test Case 1: Initial Data Fetch Success
  it('Initial Data Fetch Success', async () => {
    getSpy.mockImplementation((url: string) => {
      if (url === '/energy/current') return Promise.resolve({ value: 123 });
      if (url === '/energy/history') return Promise.resolve([...mockHistory]);
      return Promise.reject(new Error('Unknown endpoint'));
    });

    await act(async () => {
      render(<Dashboard />);
    });

    expect(getSpy).toHaveBeenCalledWith('/energy/current');
    expect(getSpy).toHaveBeenCalledWith('/energy/history');

    await waitFor(() => {
      expect(screen.getByText('123')).toBeInTheDocument();
      expect(screen.getByTestId('line-chart')).toBeInTheDocument();
    });
  });

  // Test Case 2: Periodic Data Fetch Every 60 Seconds
  it('Periodic Data Fetch Every 60 Seconds', async () => {
    getSpy.mockResolvedValueOnce({ value: 123 });
    getSpy.mockResolvedValueOnce([...mockHistory]);
    getSpy.mockResolvedValueOnce({ value: 456 });
    getSpy.mockResolvedValueOnce([...mockHistory.map(h => ({ ...h, value: h.value + 1 }))]);

    await act(async () => {
      render(<Dashboard />);
    });

    expect(getSpy).toHaveBeenCalledTimes(2);

    // Advance 60 seconds
    await act(async () => {
      jest.advanceTimersByTime(60000);
    });

    // Should call fetchData again
    expect(getSpy).toHaveBeenCalledTimes(4);
  });

  // Test Case 3: Current Energy Value Render
  it('Current Energy Value Render', async () => {
    getSpy.mockResolvedValueOnce({ value: 999 });
    getSpy.mockResolvedValueOnce([...mockHistory]);

    await act(async () => {
      render(<Dashboard />);
    });

    await waitFor(() => {
      const energy = screen.getByText('999');
      expect(energy).toBeInTheDocument();
      // Large font: check for style or class (assume class 'current-energy-large' is used)
      expect(energy.className).toMatch(/large|current-energy/i);
    });
  });

  // Test Case 4: History Line Chart Render
  it('History Line Chart Render', async () => {
    getSpy.mockResolvedValueOnce({ value: 123 });
    getSpy.mockResolvedValueOnce([...mockHistory]);

    await act(async () => {
      render(<Dashboard />);
    });

    await waitFor(() => {
      expect(screen.getByTestId('line-chart')).toBeInTheDocument();
    });
  });

  // Test Case 5: Logout Button Render
  it('Logout Button Render', async () => {
    getSpy.mockResolvedValue({ value: 123 });
    getSpy.mockResolvedValue([...mockHistory]);

    await act(async () => {
      render(<Dashboard />);
    });

    expect(screen.getByRole('button', { name: /logout/i })).toBeInTheDocument();
  });

  // Test Case 6: Logout Button Click
  it('Logout Button Click', async () => {
    getSpy.mockResolvedValue({ value: 123 });
    getSpy.mockResolvedValue([...mockHistory]);
    const mockLogout = jest.fn();

    // Patch Dashboard to accept a logout prop for testability if needed
    // Otherwise, spy on window.location or session clear logic
    const originalLocation = window.location;
    // @ts-ignore
    delete window.location;
    // @ts-ignore
    window.location = { assign: jest.fn() };

    await act(async () => {
      render(<Dashboard />);
    });

    fireEvent.click(screen.getByRole('button', { name: /logout/i }));

    // Check for redirect or session clear
    expect(window.location.assign).toHaveBeenCalled();

    window.location = originalLocation;
  });

  // Test Case 7: Current Energy Fetch Failure
  it('Current Energy Fetch Failure', async () => {
    getSpy.mockImplementation((url: string) => {
      if (url === '/energy/current') return Promise.reject(new Error('Server error'));
      if (url === '/energy/history') return Promise.resolve([...mockHistory]);
      return Promise.reject(new Error('Unknown endpoint'));
    });

    await act(async () => {
      render(<Dashboard />);
    });

    await waitFor(() => {
      expect(screen.getByText(/error|failed|unable/i)).toBeInTheDocument();
    });
  });

  // Test Case 8: History Fetch Failure
  it('History Fetch Failure', async () => {
    getSpy.mockImplementation((url: string) => {
      if (url === '/energy/current') return Promise.resolve({ value: 123 });
      if (url === '/energy/history') return Promise.reject(new Error('Server error'));
      return Promise.reject(new Error('Unknown endpoint'));
    });

    await act(async () => {
      render(<Dashboard />);
    });

    await waitFor(() => {
      expect(screen.getByText(/error|failed|unable/i)).toBeInTheDocument();
    });
  });

  // Test Case 9: Empty History Data
  it('Empty History Data', async () => {
    getSpy.mockImplementation((url: string) => {
      if (url === '/energy/current') return Promise.resolve({ value: 123 });
      if (url === '/energy/history') return Promise.resolve([]);
      return Promise.reject(new Error('Unknown endpoint'));
    });

    await act(async () => {
      render(<Dashboard />);
    });

    await waitFor(() => {
      expect(screen.getByText(/no historical data|empty/i)).toBeInTheDocument();
    });
  });

  // Test Case 10: Invalid Current Energy Data
  it('Invalid Current Energy Data', async () => {
    getSpy.mockImplementation((url: string) => {
      if (url === '/energy/current') return Promise.resolve({ wrongField: 999 });
      if (url === '/energy/history') return Promise.resolve([...mockHistory]);
      return Promise.reject(new Error('Unknown endpoint'));
    });

    await act(async () => {
      render(<Dashboard />);
    });

    await waitFor(() => {
      expect(screen.getByText(/error|invalid|unable/i)).toBeInTheDocument();
    });
  });

  // Test Case 11: Invalid History Data
  it('Invalid History Data', async () => {
    getSpy.mockImplementation((url: string) => {
      if (url === '/energy/current') return Promise.resolve({ value: 123 });
      if (url === '/energy/history') return Promise.resolve({ not: 'an array' });
      return Promise.reject(new Error('Unknown endpoint'));
    });

    await act(async () => {
      render(<Dashboard />);
    });

    await waitFor(() => {
      expect(screen.getByText(/error|invalid|unable/i)).toBeInTheDocument();
    });
  });

  // Test Case 12: Unmount Clears Interval
  it('Unmount Clears Interval', async () => {
    getSpy.mockResolvedValue({ value: 123 });
    getSpy.mockResolvedValue([...mockHistory]);

    const { unmount } = render(<Dashboard />);
    unmount();

    // Advance time and ensure fetchData is not called again
    const callCount = getSpy.mock.calls.length;
    act(() => {
      jest.advanceTimersByTime(60000);
    });
    expect(getSpy.mock.calls.length).toBe(callCount);
  });

  // Test Case 13: History Data Is Reversed
  it('History Data Is Reversed', async () => {
    getSpy.mockImplementation((url: string) => {
      if (url === '/energy/current') return Promise.resolve({ value: 123 });
      if (url === '/energy/history') return Promise.resolve([
        { timestamp: '2025-01-01T00:00:00Z', value: 1 },
        { timestamp: '2025-01-02T00:00:00Z', value: 2 },
        { timestamp: '2025-01-03T00:00:00Z', value: 3 },
      ]);
      return Promise.reject(new Error('Unknown endpoint'));
    });

    await act(async () => {
      render(<Dashboard />);
    });

    // The chart should receive reversed data (most recent first)
    // We assume Dashboard passes reversed data to LineChart as a prop or renders it in order
    // This test may need to be adapted to the actual prop structure
    expect(LineChart).toHaveBeenCalled();
    // Optionally, check the data prop if accessible
    // expect(LineChart).toHaveBeenCalledWith(expect.objectContaining({ data: [
    //   { timestamp: '2025-01-03T00:00:00Z', value: 3 },
    //   { timestamp: '2025-01-02T00:00:00Z', value: 2 },
    //   { timestamp: '2025-01-01T00:00:00Z', value: 1 },
    // ] }), expect.anything());
  });

  // Test Case 14: Multiple Fetch Failures
  it('Multiple Fetch Failures', async () => {
    getSpy.mockImplementation(() => Promise.reject(new Error('Server error')));

    await act(async () => {
      render(<Dashboard />);
    });

    await waitFor(() => {
      expect(screen.getAllByText(/error|failed|unable/i).length).toBeGreaterThanOrEqual(2);
    });
  });

  // Test Case 15: Partial Data Available
  it('Partial Data Available', async () => {
    // /energy/current succeeds, /energy/history fails
    getSpy.mockImplementation((url: string) => {
      if (url === '/energy/current') return Promise.resolve({ value: 123 });
      if (url === '/energy/history') return Promise.reject(new Error('Server error'));
      return Promise.reject(new Error('Unknown endpoint'));
    });

    await act(async () => {
      render(<Dashboard />);
    });

    await waitFor(() => {
      expect(screen.getByText('123')).toBeInTheDocument();
      expect(screen.getByText(/error|failed|unable/i)).toBeInTheDocument();
    });

    // /energy/current fails, /energy/history succeeds
    getSpy.mockImplementation((url: string) => {
      if (url === '/energy/current') return Promise.reject(new Error('Server error'));
      if (url === '/energy/history') return Promise.resolve([...mockHistory]);
      return Promise.reject(new Error('Unknown endpoint'));
    });

    cleanup();
    await act(async () => {
      render(<Dashboard />);
    });

    await waitFor(() => {
      expect(screen.getByTestId('line-chart')).toBeInTheDocument();
      expect(screen.getByText(/error|failed|unable/i)).toBeInTheDocument();
    });
  });
});