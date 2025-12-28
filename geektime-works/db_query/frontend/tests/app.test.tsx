/** Basic component smoke tests */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { SqlEditor } from '../src/components/SqlEditor';

describe('Component Smoke Tests', () => {
  it('SqlEditor renders without crashing', () => {
    render(<SqlEditor value="SELECT * FROM users" onChange={() => {}} />);
    expect(screen.getByRole('textbox')).toBeInTheDocument();
  });

  it('SqlEditor displays initial value', () => {
    render(<SqlEditor value="SELECT * FROM users" onChange={() => {}} />);
    const editor = screen.getByRole('textbox');
    expect(editor).toHaveProperty('value', 'SELECT * FROM users');
  });
});
