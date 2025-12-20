---
applyTo:
  - pattern: "src/player_experience/**/*.{jsx,tsx,ts,js}"
  - pattern: "**/*.{jsx,tsx}"
  - pattern: "**/*.css"
tags: ["typescript", "react", "frontend", "ui", "accessibility"]
description: "React/TypeScript coding standards, component patterns, and UI/UX guidelines for TTA player experience"
---

# Frontend React/TypeScript Standards

## Overview

This instruction set defines standards for React/TypeScript development in TTA's player experience layer. All frontend code must prioritize accessibility, performance, and user experience.

## Core Principles

### 1. Component Design
- Keep components small and focused (single responsibility)
- Use functional components with hooks
- Implement proper prop typing with TypeScript
- Document component purpose and usage

### 2. Accessibility
- Follow WCAG 2.1 AA standards
- Use semantic HTML elements
- Implement proper ARIA labels
- Test with screen readers
- Ensure keyboard navigation

### 3. Performance
- Optimize re-renders with React.memo
- Use lazy loading for code splitting
- Minimize bundle size
- Implement proper caching strategies

## Implementation Standards

### Component Structure

```typescript
import React, { FC, ReactNode } from 'react';

interface PlayerInputProps {
  playerId: string;
  onSubmit: (input: string) => Promise<void>;
  disabled?: boolean;
  placeholder?: string;
}

/**
 * PlayerInput component for therapeutic text adventure.
 *
 * @param props - Component props
 * @returns React component
 */
const PlayerInput: FC<PlayerInputProps> = ({
  playerId,
  onSubmit,
  disabled = false,
  placeholder = "Enter your response..."
}) => {
  const [input, setInput] = React.useState('');
  const [isLoading, setIsLoading] = React.useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      await onSubmit(input);
      setInput('');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} aria-label="Player input form">
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        disabled={disabled || isLoading}
        placeholder={placeholder}
        aria-label="Player response input"
        required
      />
      <button
        type="submit"
        disabled={disabled || isLoading}
        aria-busy={isLoading}
      >
        {isLoading ? 'Sending...' : 'Submit'}
      </button>
    </form>
  );
};

export default PlayerInput;
```

### TypeScript Best Practices

```typescript
// ✅ Correct: Proper typing
interface GameState {
  playerId: string;
  narrative: string;
  playerInput: string;
  aiResponse: string;
  isLoading: boolean;
}

// ✅ Correct: Type-safe props
const GameComponent: FC<{ state: GameState }> = ({ state }) => {
  // Implementation
};

// ❌ Incorrect: Any types
const GameComponent = ({ state }: any) => {
  // Implementation
};
```

## Testing Requirements

### Unit Tests
- Test component rendering
- Test user interactions
- Test prop variations
- Minimum 80% coverage

### Integration Tests
- Test component interactions
- Test API integration
- Test state management
- Test error handling

### E2E Tests (Playwright)
```typescript
test('player can submit input', async ({ page }) => {
  await page.goto('/game');
  await page.fill('input[aria-label="Player response input"]', 'Hello');
  await page.click('button:has-text("Submit")');
  await expect(page.locator('text=AI Response')).toBeVisible();
});
```

## Accessibility Checklist

- [ ] Semantic HTML used throughout
- [ ] ARIA labels for interactive elements
- [ ] Keyboard navigation working
- [ ] Color contrast meets WCAG AA
- [ ] Focus indicators visible
- [ ] Screen reader tested
- [ ] Form labels associated
- [ ] Error messages accessible

## Code Style

### Formatting
- **Formatter**: Prettier (line length: 80)
- **Linting**: ESLint with React plugin
- **Type Checking**: TypeScript strict mode

### Naming Conventions
- **Components**: PascalCase (e.g., `PlayerInput`)
- **Functions**: camelCase (e.g., `handleSubmit`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `MAX_INPUT_LENGTH`)
- **Files**: Match component name (e.g., `PlayerInput.tsx`)

## Performance Optimization

### Memoization
```typescript
// ✅ Correct: Memoize expensive components
const PlayerCard = React.memo(({ player }: { player: Player }) => {
  return <div>{player.name}</div>;
});
```

### Code Splitting
```typescript
// ✅ Correct: Lazy load components
const GameBoard = React.lazy(() => import('./GameBoard'));

<Suspense fallback={<Loading />}>
  <GameBoard />
</Suspense>
```

## Common Patterns

### Custom Hooks
```typescript
// ✅ Correct: Custom hook for reusable logic
function usePlayerInput() {
  const [input, setInput] = React.useState('');
  const [isLoading, setIsLoading] = React.useState(false);

  const submit = async (onSubmit: (input: string) => Promise<void>) => {
    setIsLoading(true);
    try {
      await onSubmit(input);
      setInput('');
    } finally {
      setIsLoading(false);
    }
  };

  return { input, setInput, isLoading, submit };
}
```

## Code Review Checklist

- [ ] TypeScript strict mode enabled
- [ ] Props properly typed
- [ ] Accessibility standards met
- [ ] Performance optimized
- [ ] Tests passing (>80% coverage)
- [ ] ESLint/Prettier passing
- [ ] Documentation updated
- [ ] No console errors/warnings

## References

- React Documentation: https://react.dev/
- TypeScript Handbook: https://www.typescriptlang.org/docs/
- WCAG 2.1: https://www.w3.org/WAI/WCAG21/quickref/
- Playwright Testing: https://playwright.dev/
