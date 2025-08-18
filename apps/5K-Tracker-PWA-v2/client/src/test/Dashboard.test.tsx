import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider } from '../context/ThemeContext';
import { Dashboard } from '../pages/Dashboard';

const renderWithProviders = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      <ThemeProvider>
        {component}
      </ThemeProvider>
    </BrowserRouter>
  );
};

describe('Dashboard Component', () => {
  test('renders dashboard heading', () => {
    renderWithProviders(<Dashboard />);
    expect(screen.getByRole('heading', { name: /dashboard/i })).toBeInTheDocument();
  });

  test('displays stats cards', () => {
    renderWithProviders(<Dashboard />);
    expect(screen.getByText('Total Runs')).toBeInTheDocument();
    expect(screen.getByText('Best 5K Time')).toBeInTheDocument();
    expect(screen.getByText('This Month')).toBeInTheDocument();
    expect(screen.getByText('Favorite Location')).toBeInTheDocument();
  });

  test('shows recent races section', () => {
    renderWithProviders(<Dashboard />);
    expect(screen.getByText('Recent Races')).toBeInTheDocument();
  });
});