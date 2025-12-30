/**
 * @file .codevalid/tests/user_onboarding/frontend_register_component.ts
 * @description Tests for Register component (frontend/src/views/Register.tsx)
 * Jest + React Testing Library + MSW for API mocking
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { rest } from 'msw';
import { setupServer } from 'msw/node';
import { BrowserRouter, MemoryRouter } from 'react-router-dom';
import Register from '../../../frontend/src/views/Register';

// Mock for navigation (react-router-dom v6+)
const mockedNavigate = jest.fn();
jest.mock('react-router-dom', () => {
  const actual = jest.requireActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockedNavigate,
  };
});

// MSW server for API mocking
const server = setupServer();

beforeAll(() => server.listen());
afterEach(() => {
  server.resetHandlers();
  mockedNavigate.mockReset();
});
afterAll(() => server.close());

function renderWithRouter(ui: React.ReactElement) {
  return render(<MemoryRouter>{ui}</MemoryRouter>);
}

// Utility: create a file of given type and size
function createFile(name: string, type: string, size: number) {
  const file = new File(['a'.repeat(size)], name, { type });
  Object.defineProperty(file, 'size', { value: size });
  return file;
}

// --- TESTS ---

describe('Register component', () => {
  // Test Case 1: Render Registration Form
  it('Render Registration Form', () => {
    renderWithRouter(<Register />);
    expect(screen.getByLabelText(/full name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /submit/i })).toBeInTheDocument();
  });

  // Test Case 2: Successful Registration Submission
  it('Successful Registration Submission', async () => {
    server.use(
      rest.post('/auth/register', (req, res, ctx) => {
        return res(ctx.status(200), ctx.json({ success: true }));
      })
    );
    renderWithRouter(<Register />);
    userEvent.type(screen.getByLabelText(/full name/i), 'John Doe');
    userEvent.type(screen.getByLabelText(/email/i), 'john@example.com');
    userEvent.type(screen.getByLabelText(/password/i), 'StrongPass123');
    fireEvent.click(screen.getByRole('button', { name: /submit/i }));

    await waitFor(() => {
      expect(mockedNavigate).toHaveBeenCalledWith('/login');
    });
  });

  // Test Case 3: Submission with Empty Fields
  it('Submission with Empty Fields', async () => {
    renderWithRouter(<Register />);
    fireEvent.click(screen.getByRole('button', { name: /submit/i }));
    expect(await screen.findAllByText(/required/i)).not.toHaveLength(0);
    expect(mockedNavigate).not.toHaveBeenCalled();
  });

  // Test Case 4: Submission with Invalid Email
  it('Submission with Invalid Email', async () => {
    renderWithRouter(<Register />);
    userEvent.type(screen.getByLabelText(/full name/i), 'Jane Doe');
    userEvent.type(screen.getByLabelText(/email/i), 'invalid-email');
    userEvent.type(screen.getByLabelText(/password/i), 'StrongPass123');
    fireEvent.click(screen.getByRole('button', { name: /submit/i }));
    expect(await screen.findByText(/invalid email/i)).toBeInTheDocument();
    expect(mockedNavigate).not.toHaveBeenCalled();
  });

  // Test Case 5: Submission with Short Password
  it('Submission with Short Password', async () => {
    renderWithRouter(<Register />);
    userEvent.type(screen.getByLabelText(/full name/i), 'Jane Doe');
    userEvent.type(screen.getByLabelText(/email/i), 'jane@example.com');
    userEvent.type(screen.getByLabelText(/password/i), '123');
    fireEvent.click(screen.getByRole('button', { name: /submit/i }));
    expect(await screen.findByText(/password.*too short/i)).toBeInTheDocument();
    expect(mockedNavigate).not.toHaveBeenCalled();
  });

  // Test Case 6: Submission with Duplicate Email
  it('Submission with Duplicate Email', async () => {
    server.use(
      rest.post('/auth/register', (req, res, ctx) => {
        return res(ctx.status(409), ctx.json({ error: 'Email already exists' }));
      })
    );
    renderWithRouter(<Register />);
    userEvent.type(screen.getByLabelText(/full name/i), 'Jane Doe');
    userEvent.type(screen.getByLabelText(/email/i), 'duplicate@example.com');
    userEvent.type(screen.getByLabelText(/password/i), 'StrongPass123');
    fireEvent.click(screen.getByRole('button', { name: /submit/i }));
    expect(await screen.findByText(/email already exists/i)).toBeInTheDocument();
    expect(mockedNavigate).not.toHaveBeenCalled();
  });

  // Test Case 7: Network/API Error Handling
  it('Network/API Error Handling', async () => {
    server.use(
      rest.post('/auth/register', (req, res, ctx) => {
        return res(ctx.status(500), ctx.json({ error: 'Server error' }));
      })
    );
    renderWithRouter(<Register />);
    userEvent.type(screen.getByLabelText(/full name/i), 'Jane Doe');
    userEvent.type(screen.getByLabelText(/email/i), 'jane@example.com');
    userEvent.type(screen.getByLabelText(/password/i), 'StrongPass123');
    fireEvent.click(screen.getByRole('button', { name: /submit/i }));
    expect(await screen.findByText(/server error/i)).toBeInTheDocument();
    expect(mockedNavigate).not.toHaveBeenCalled();
  });

  // Test Case 8: Password Visibility Toggle
  it('Password Visibility Toggle', async () => {
    renderWithRouter(<Register />);
    const passwordInput = screen.getByLabelText(/password/i);
    const toggleBtn = screen.getByLabelText(/toggle password visibility/i);
    // Initially type should be password
    expect(passwordInput).toHaveAttribute('type', 'password');
    fireEvent.click(toggleBtn);
    expect(passwordInput).toHaveAttribute('type', 'text');
    fireEvent.click(toggleBtn);
    expect(passwordInput).toHaveAttribute('type', 'password');
  });

  // Test Case 9: Dashboard Link Present
  it('Dashboard Link Present', () => {
    renderWithRouter(<Register />);
    const dashboardLink = screen.getByRole('link', { name: /dashboard/i });
    expect(dashboardLink).toBeInTheDocument();
  });

  // Test Case 10: Dashboard Link Navigation
  it('Dashboard Link Navigation', () => {
    renderWithRouter(<Register />);
    const dashboardLink = screen.getByRole('link', { name: /dashboard/i });
    userEvent.click(dashboardLink);
    expect(mockedNavigate).toHaveBeenCalledWith('/dashboard');
  });

  // Test Case 11: Upload Valid Image File
  it('Upload Valid Image File', async () => {
    renderWithRouter(<Register />);
    const fileInput = screen.getByLabelText(/upload/i);
    const file = createFile('pic.jpg', 'image/jpeg', 1024 * 1024); // 1MB
    userEvent.upload(fileInput, file);
    expect(await screen.findByText(/file accepted/i)).toBeInTheDocument();
  });

  // Test Case 12: Upload Valid PDF File
  it('Upload Valid PDF File', async () => {
    renderWithRouter(<Register />);
    const fileInput = screen.getByLabelText(/upload/i);
    const file = createFile('doc.pdf', 'application/pdf', 1024 * 1024); // 1MB
    userEvent.upload(fileInput, file);
    expect(await screen.findByText(/file accepted/i)).toBeInTheDocument();
  });

  // Test Case 13: Upload Invalid File Type
  it('Upload Invalid File Type', async () => {
    renderWithRouter(<Register />);
    const fileInput = screen.getByLabelText(/upload/i);
    const file = createFile('malware.exe', 'application/x-msdownload', 1024 * 1024);
    userEvent.upload(fileInput, file);
    expect(await screen.findByText(/unsupported file type/i)).toBeInTheDocument();
  });

  // Test Case 14: Upload File Exceeding Size Limit
  it('Upload File Exceeding Size Limit', async () => {
    renderWithRouter(<Register />);
    const fileInput = screen.getByLabelText(/upload/i);
    const file = createFile('bigfile.jpg', 'image/jpeg', 6 * 1024 * 1024); // 6MB
    userEvent.upload(fileInput, file);
    expect(await screen.findByText(/file size.*exceeds/i)).toBeInTheDocument();
  });

  // Test Case 15: Skip File Upload and Access Dashboard
  it('Skip File Upload and Access Dashboard', async () => {
    server.use(
      rest.post('/auth/register', (req, res, ctx) => {
        return res(ctx.status(200), ctx.json({ success: true }));
      })
    );
    renderWithRouter(<Register />);
    userEvent.type(screen.getByLabelText(/full name/i), 'Jane Doe');
    userEvent.type(screen.getByLabelText(/email/i), 'jane@example.com');
    userEvent.type(screen.getByLabelText(/password/i), 'StrongPass123');
    fireEvent.click(screen.getByRole('button', { name: /submit/i }));
    await waitFor(() => {
      expect(mockedNavigate).toHaveBeenCalledWith('/login');
    });
    // Simulate user clicking dashboard link after registration
    renderWithRouter(<Register />);
    const dashboardLink = screen.getByRole('link', { name: /dashboard/i });
    userEvent.click(dashboardLink);
    expect(mockedNavigate).toHaveBeenCalledWith('/dashboard');
  });

  // Test Case 16: Upload Multiple Valid Files
  it('Upload Multiple Valid Files', async () => {
    renderWithRouter(<Register />);
    const fileInput = screen.getByLabelText(/upload/i);
    const image = createFile('pic.jpg', 'image/jpeg', 1024 * 1024);
    const pdf = createFile('doc.pdf', 'application/pdf', 1024 * 1024);
    userEvent.upload(fileInput, [image, pdf]);
    expect(await screen.findByText(/2 files accepted/i)).toBeInTheDocument();
  });

  // Test Case 17: Form Reset After Successful Registration
  it('Form Reset After Successful Registration', async () => {
    server.use(
      rest.post('/auth/register', (req, res, ctx) => {
        return res(ctx.status(200), ctx.json({ success: true }));
      })
    );
    renderWithRouter(<Register />);
    const nameInput = screen.getByLabelText(/full name/i);
    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    userEvent.type(nameInput, 'Jane Doe');
    userEvent.type(emailInput, 'jane@example.com');
    userEvent.type(passwordInput, 'StrongPass123');
    fireEvent.click(screen.getByRole('button', { name: /submit/i }));
    await waitFor(() => {
      expect(nameInput).toHaveValue('');
      expect(emailInput).toHaveValue('');
      expect(passwordInput).toHaveValue('');
    });
  });

  // Test Case 18: Loading State During Submission
  it('Loading State During Submission', async () => {
    let resolveRequest: () => void;
    server.use(
      rest.post('/auth/register', () => {
        return new Promise((resolve) => {
          resolveRequest = () => resolve([200, { success: true }]);
        });
      })
    );
    renderWithRouter(<Register />);
    userEvent.type(screen.getByLabelText(/full name/i), 'Jane Doe');
    userEvent.type(screen.getByLabelText(/email/i), 'jane@example.com');
    userEvent.type(screen.getByLabelText(/password/i), 'StrongPass123');
    fireEvent.click(screen.getByRole('button', { name: /submit/i }));
    expect(screen.getByRole('button', { name: /submit/i })).toBeDisabled();
    expect(screen.getByTestId('loading-indicator')).toBeInTheDocument();
    // Simulate request finishing
    resolveRequest();
  });
});