import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider } from '../auth/AuthContext';
import App from '../App';

function renderApp(route = '/') {
  return render(
    <MemoryRouter initialEntries={[route]}>
      <AuthProvider>
        <App />
      </AuthProvider>
    </MemoryRouter>,
  );
}

describe('App', () => {
  it('mounts without crashing', () => {
    const { container } = renderApp();
    expect(container).toBeTruthy();
  });

  it('redirects unauthenticated users to login', () => {
    renderApp('/');
    // When not authenticated the app should show the login page with its heading
    expect(screen.getByRole('heading', { name: 'Login' })).toBeTruthy();
  });
});
