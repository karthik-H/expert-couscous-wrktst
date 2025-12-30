import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Onboarding from '../../../frontend/src/views/Onboarding';
import { BrowserRouter } from 'react-router-dom';

// Mock API and navigation
jest.mock('../../../frontend/src/api/client', () => ({
  post: jest.fn(),
}));
import apiClient from '../../../frontend/src/api/client';

const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => {
  const actual = jest.requireActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    Link: (props: any) => <a href={props.to} {...props} />,
  };
});

function renderWithRouter(ui: React.ReactElement) {
  return render(<BrowserRouter>{ui}</BrowserRouter>);
}

function createFile(name: string, type: string, size = 1024) {
  const file = new File(['a'.repeat(size)], name, { type });
  Object.defineProperty(file, 'size', { value: size });
  return file;
}

describe('Onboarding Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  // Test Case 1
  it('renders_form_elements', () => {
    renderWithRouter(<Onboarding />);
    expect(screen.getByLabelText(/energy source picture/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/supporting document/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /submit/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /skip/i })).toBeInTheDocument();
  });

  // Test Case 2
  it('submit_with_valid_files', async () => {
    (apiClient.post as jest.Mock).mockResolvedValueOnce({ data: { message: 'Success' } });
    renderWithRouter(<Onboarding />);
    const picture = createFile('energy.jpeg', 'image/jpeg');
    const doc = createFile('support.pdf', 'application/pdf');
    userEvent.upload(screen.getByLabelText(/energy source picture/i), picture);
    userEvent.upload(screen.getByLabelText(/supporting document/i), doc);
    userEvent.click(screen.getByRole('button', { name: /submit/i }));

    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalledWith(
        '/onboarding/upload',
        expect.any(FormData),
        expect.any(Object)
      );
      expect(screen.getByText(/success/i)).toBeInTheDocument();
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
    });
  });

  // Test Case 3
  it('submit_with_only_picture', async () => {
    (apiClient.post as jest.Mock).mockResolvedValueOnce({ data: { message: 'Success' } });
    renderWithRouter(<Onboarding />);
    const picture = createFile('energy.jpeg', 'image/jpeg');
    userEvent.upload(screen.getByLabelText(/energy source picture/i), picture);
    userEvent.click(screen.getByRole('button', { name: /submit/i }));

    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalledWith(
        '/onboarding/upload',
        expect.any(FormData),
        expect.any(Object)
      );
      expect(screen.getByText(/success/i)).toBeInTheDocument();
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
    });
  });

  // Test Case 4
  it('submit_with_only_document', async () => {
    (apiClient.post as jest.Mock).mockResolvedValueOnce({ data: { message: 'Success' } });
    renderWithRouter(<Onboarding />);
    const doc = createFile('support.pdf', 'application/pdf');
    userEvent.upload(screen.getByLabelText(/supporting document/i), doc);
    userEvent.click(screen.getByRole('button', { name: /submit/i }));

    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalledWith(
        '/onboarding/upload',
        expect.any(FormData),
        expect.any(Object)
      );
      expect(screen.getByText(/success/i)).toBeInTheDocument();
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
    });
  });

  // Test Case 5
  it('skip_upload', async () => {
    (apiClient.post as jest.Mock).mockResolvedValueOnce({ data: { message: 'Success' } });
    renderWithRouter(<Onboarding />);
    userEvent.click(screen.getByRole('button', { name: /skip/i }));

    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalledWith(
        '/onboarding/upload',
        expect.any(FormData),
        expect.any(Object)
      );
      expect(screen.getByText(/success/i)).toBeInTheDocument();
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
    });
  });

  // Test Case 6
  it('submit_with_invalid_picture_type', async () => {
    renderWithRouter(<Onboarding />);
    const invalidFile = createFile('energy.txt', 'text/plain');
    userEvent.upload(screen.getByLabelText(/energy source picture/i), invalidFile);
    userEvent.click(screen.getByRole('button', { name: /submit/i }));

    await waitFor(() => {
      expect(screen.getByText(/invalid file type/i)).toBeInTheDocument();
      expect(apiClient.post).not.toHaveBeenCalled();
    });
  });

  // Test Case 7
  it('submit_with_invalid_document_type', async () => {
    renderWithRouter(<Onboarding />);
    const invalidFile = createFile('support.exe', 'application/x-msdownload');
    userEvent.upload(screen.getByLabelText(/supporting document/i), invalidFile);
    userEvent.click(screen.getByRole('button', { name: /submit/i }));

    await waitFor(() => {
      expect(screen.getByText(/invalid file type/i)).toBeInTheDocument();
      expect(apiClient.post).not.toHaveBeenCalled();
    });
  });

  // Test Case 8
  it('submit_with_picture_too_large', async () => {
    renderWithRouter(<Onboarding />);
    const largeFile = createFile('energy.jpeg', 'image/jpeg', 6 * 1024 * 1024);
    userEvent.upload(screen.getByLabelText(/energy source picture/i), largeFile);
    userEvent.click(screen.getByRole('button', { name: /submit/i }));

    await waitFor(() => {
      expect(screen.getByText(/file size exceeds/i)).toBeInTheDocument();
      expect(apiClient.post).not.toHaveBeenCalled();
    });
  });

  // Test Case 9
  it('submit_with_document_too_large', async () => {
    renderWithRouter(<Onboarding />);
    const largeFile = createFile('support.pdf', 'application/pdf', 6 * 1024 * 1024);
    userEvent.upload(screen.getByLabelText(/supporting document/i), largeFile);
    userEvent.click(screen.getByRole('button', { name: /submit/i }));

    await waitFor(() => {
      expect(screen.getByText(/file size exceeds/i)).toBeInTheDocument();
      expect(apiClient.post).not.toHaveBeenCalled();
    });
  });

  // Test Case 10
  it('submit_network_error', async () => {
    (apiClient.post as jest.Mock).mockRejectedValueOnce(new Error('Network Error'));
    renderWithRouter(<Onboarding />);
    const picture = createFile('energy.jpeg', 'image/jpeg');
    userEvent.upload(screen.getByLabelText(/energy source picture/i), picture);
    userEvent.click(screen.getByRole('button', { name: /submit/i }));

    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalled();
      expect(screen.getByText(/error/i)).toBeInTheDocument();
      expect(mockNavigate).not.toHaveBeenCalled();
    });
  });

  // Test Case 11
  it('skip_network_error', async () => {
    (apiClient.post as jest.Mock).mockRejectedValueOnce(new Error('Network Error'));
    renderWithRouter(<Onboarding />);
    userEvent.click(screen.getByRole('button', { name: /skip/i }));

    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalled();
      expect(screen.getByText(/error/i)).toBeInTheDocument();
      expect(mockNavigate).not.toHaveBeenCalled();
    });
  });

  // Test Case 12
  it('submit_multiple_times', async () => {
    (apiClient.post as jest.Mock).mockResolvedValueOnce({ data: { message: 'Success' } });
    renderWithRouter(<Onboarding />);
    const picture = createFile('energy.jpeg', 'image/jpeg');
    userEvent.upload(screen.getByLabelText(/energy source picture/i), picture);

    const submitBtn = screen.getByRole('button', { name: /submit/i });
    userEvent.click(submitBtn);
    userEvent.click(submitBtn);
    userEvent.click(submitBtn);

    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalledTimes(1);
      expect(submitBtn).toBeDisabled();
    });
  });

  // Test Case 13
  it('skip_multiple_times', async () => {
    (apiClient.post as jest.Mock).mockResolvedValueOnce({ data: { message: 'Success' } });
    renderWithRouter(<Onboarding />);
    const skipBtn = screen.getByRole('button', { name: /skip/i });
    userEvent.click(skipBtn);
    userEvent.click(skipBtn);
    userEvent.click(skipBtn);

    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalledTimes(1);
      expect(skipBtn).toBeDisabled();
    });
  });

  // Test Case 14
  it('file_input_reset_after_submit', async () => {
    (apiClient.post as jest.Mock).mockResolvedValueOnce({ data: { message: 'Success' } });
    renderWithRouter(<Onboarding />);
    const pictureInput = screen.getByLabelText(/energy source picture/i) as HTMLInputElement;
    const docInput = screen.getByLabelText(/supporting document/i) as HTMLInputElement;
    const picture = createFile('energy.jpeg', 'image/jpeg');
    const doc = createFile('support.pdf', 'application/pdf');
    userEvent.upload(pictureInput, picture);
    userEvent.upload(docInput, doc);
    userEvent.click(screen.getByRole('button', { name: /submit/i }));

    await waitFor(() => {
      expect(pictureInput.value).toBe('');
      expect(docInput.value).toBe('');
    });
  });

  // Test Case 15
  it('dashboard_link_present', () => {
    renderWithRouter(<Onboarding />);
    const dashboardLink = screen.getByRole('link', { name: /dashboard/i });
    expect(dashboardLink).toBeInTheDocument();
    // Simulate click
    userEvent.click(dashboardLink);
    expect(dashboardLink).toHaveAttribute('href', '/dashboard');
  });
});