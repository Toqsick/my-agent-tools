---
name: ui-component-library
description: "Use when user asks for component library scaffolding, button/input/card components, reusable UI primitives. NOT for full app pages or one-off bespoke components. Scaffold a component library (buttons, inputs, cards, modals)."
version: 1.0.0
author: Yuno (Hermes Agent) — based on KIMI K2 UI-Factory-Pattern 2026-06-30
license: MIT
metadata:
  hermes:
    tags:
    - ui
    - components
    - library
    - react
    - vue
    - svelte
    - primitives
    - button
    - modal
    - card
    - nav
    related_skills:
    - ui-design-system
    - ui-color-system
    - ui-dashboard
    - ui-factory
    - web-design-guidelines
    part_of: ui-factory
    triggers:
    - component library
    - UI kit
    - Button bauen
    - Modal bauen
    - Card bauen
    - Nav bauen
    - scaffold components
    - standardize UI primitives
    - wiederverwendbare Komponenten
    - Form-Component
    - Input bauen
    - Storybook
lane: worker-vision
reasoning_effort: xhigh
trigger_keywords: ['component', 'library', 'components', 'ui-component-library', 'scaffolding']
keywords: ['component', 'library', 'components', 'user', 'asks']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['session-state-audit']
---


## 🚨 AUTO-TRIGGER

Dieser Skill triggert **automatisch** wenn Bastis Input nach UI-Components fragt. Auch ohne expliziten Aufruf — wenn die Trigger-Phrasen matchen, wird dieser Skill geladen.

**Trigger-Keywords (deutsch + englisch):** component library, UI kit, Button, Modal, Card, Nav, Form, Input, scaffold, Storybook, wiederverwendbare Komponenten, Primitives, Buttons bauen, alle Components, alle UI-Elemente

Wenn Basti nach **mehreren UI-Aspekten** fragt (z.B. "komplettes UI mit Components + Dashboard + Tokens"), wird stattdessen `ui-factory` getriggert (orchestriert die ganze Chain).

# ui-component-library

> **Atom:** Scaffolds a complete component library (Button, Input, Card, Modal, Nav, Badge, Avatar, etc.) from a design system. Output: framework-ready code with full a11y.

## When to use

- User asks for "component library", "UI kit", "design system components"
- Starting a new project and want reusable primitives
- Want to standardize buttons/forms/cards across an app
- Need to document components with Storybook-style examples

## Inputs

```yaml
design_system: "~/.hermes/skills/creative/ui-design-system/tokens.json OR inline tokens"
framework: "vanilla-html | react | vue | svelte | sveltekit"
style: "css-modules | tailwind | vanilla-extract | plain-css"
a11y_level: "AA | AAA"
component_set: ["button", "input", "card", "modal", "nav", "badge", "avatar", "tooltip", "tabs"]  # default core
```

## Output

**Per component:**
- `<Component>.tsx` (or `.vue`/`.svelte`) — implementation
- `<Component>.module.css` (or scoped styles) — styles
- `<Component>.stories.tsx` — Storybook story with controls
- `<Component>.test.tsx` — interaction tests
- `<Component>.a11y.test.tsx` — jest-axe a11y assertions

## Workflow

### Step 1: Design-System-Loading (30 sec)

Load tokens from `ui-design-system` skill. If no tokens provided, run `ui-design-system` first.

Parse tokens into runtime constants:
```typescript
import tokens from './tokens.json';
export const color = tokens.color;
export const space = tokens.space;
// ...
```

### Step 2: Component-Selection (1 min)

Choose components to scaffold. Default **Core-Set** (always included):
1. **Button** (variants: primary/secondary/ghost/danger, sizes: sm/md/lg, states: default/hover/active/disabled/loading)
2. **Input** (text/email/password/number/textarea, with label, helper, error)
3. **Card** (with header/body/footer, optional media, hoverable variant)
4. **Badge** (variants: neutral/primary/success/warning/error, sizes: sm/md)
5. **Avatar** (with image fallback, sizes, status indicator)

**Extended-Set** (opt-in):
6. **Modal** (with focus-trap, ESC-to-close, click-outside, ARIA dialog)
7. **Nav** (top-bar + sidebar, responsive, mobile-drawer)
8. **Tooltip** (with delay, positioning, ARIA-describedby)
9. **Tabs** (keyboard arrow-nav, ARIA tablist)
10. **Toast** (queue, auto-dismiss, swipe-to-dismiss, ARIA live-region)

### Step 3: Per-Component-Build (5-10 min per component)

Each component follows this skeleton:

```typescript
// Button.tsx
import { forwardRef, ButtonHTMLAttributes } from 'react';
import styles from './Button.module.css';
import { color, space, radius } from '../tokens';

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';
export type ButtonSize = 'sm' | 'md' | 'lg';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = 'primary', size = 'md', loading, leftIcon, rightIcon, children, disabled, className, ...rest }, ref) => {
    return (
      <button
        ref={ref}
        className={[styles.button, styles[variant], styles[size], className].filter(Boolean).join(' ')}
        disabled={disabled || loading}
        aria-busy={loading || undefined}
        {...rest}
      >
        {leftIcon && <span className={styles.icon}>{leftIcon}</span>}
        <span>{children}</span>
        {rightIcon && <span className={styles.icon}>{rightIcon}</span>}
        {loading && <span className={styles.spinner} aria-hidden="true" />}
      </button>
    );
  }
);
Button.displayName = 'Button';
```

### Step 4: Accessibility (in every component)

Mandatory checklist:

- [ ] **Semantic HTML** — `<button>` not `<div onClick>`, `<nav>` not `<div>`
- [ ] **Keyboard support** — Tab/Enter/Space work as expected
- [ ] **Focus visible** — `:focus-visible { outline: 2px solid var(--color-primary-500); }`
- [ ] **ARIA labels** — `aria-label`, `aria-labelledby`, `aria-describedby` where needed
- [ ] **Disabled state** — `disabled` attribute, not just CSS (`aria-disabled` for fake-disabled)
- [ ] **Loading state** — `aria-busy="true"`, screen-reader announces "loading"
- [ ] **Color contrast** — All text passes AA (4.5:1) or AAA (7:1)
- [ ] **Touch target** — Minimum 44x44px on mobile
- [ ] **Screen reader text** — `sr-only` class for icon-only buttons

### Step 5: Storybook-Story (1-2 min per component)

```typescript
// Button.stories.tsx
import type { Meta, StoryObj } from '@storybook/react';
import { Button } from './Button';

const meta: Meta<typeof Button> = {
  title: 'Core/Button',
  component: Button,
  argTypes: {
    variant: { control: 'select', options: ['primary', 'secondary', 'ghost', 'danger'] },
    size: { control: 'radio', options: ['sm', 'md', 'lg'] },
    loading: { control: 'boolean' },
    disabled: { control: 'boolean' },
  },
};
export default meta;

export const Primary: StoryObj<typeof Button> = { args: { variant: 'primary' } };
export const Secondary: StoryObj<typeof Button> = { args: { variant: 'secondary' } };
export const WithIcons: StoryObj<typeof Button> = {
  args: { variant: 'primary', leftIcon: '←', rightIcon: '→' },
};
export const Loading: StoryObj<typeof Button> = { args: { loading: true } };
export const Disabled: StoryObj<typeof Button> = { args: { disabled: true } };
```

### Step 6: Tests (1-2 min per component)

**Interaction tests:**
```typescript
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Button } from './Button';

test('calls onClick when clicked', async () => {
  const handleClick = jest.fn();
  render(<Button onClick={handleClick}>Click me</Button>);
  await userEvent.click(screen.getByRole('button'));
  expect(handleClick).toHaveBeenCalledTimes(1);
});

test('does not call onClick when disabled', async () => {
  const handleClick = jest.fn();
  render(<Button disabled onClick={handleClick}>Click me</Button>);
  await userEvent.click(screen.getByRole('button'));
  expect(handleClick).not.toHaveBeenCalled();
});

test('shows loading spinner and aria-busy', () => {
  render(<Button loading>Click me</Button>);
  expect(screen.getByRole('button')).toHaveAttribute('aria-busy', 'true');
});
```

**A11y tests:**
```typescript
import { render } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { Button } from './Button';

expect.extend(toHaveNoViolations);

test('has no a11y violations', async () => {
  const { container } = render(<Button>Click me</Button>);
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
```

### Step 7: Index-Export (30 sec)

```typescript
// index.ts
export { Button } from './Button';
export { Input } from './Input';
export { Card } from './Card';
export { Badge } from './Badge';
export { Avatar } from './Avatar';
// ...

export type { ButtonProps, ButtonVariant, ButtonSize } from './Button';
export type { InputProps } from './Input';
// ...
```

## Validation Checklist

- [ ] All components import tokens (no hardcoded colors/sizes)
- [ ] Every component has a Storybook story with controls
- [ ] Every component has jest-axe a11y test (zero violations)
- [ ] Every interactive component has keyboard handlers
- [ ] All buttons have visible focus indicator
- [ ] All form inputs have associated `<label>`
- [ ] All modals have focus-trap + ESC-handler
- [ ] All toasts use `aria-live="polite"` or `assertive`
- [ ] All icons are `aria-hidden="true"` (decorative) or have `aria-label`

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Using `<div onClick>` for buttons | Use `<button onClick>` — semantic HTML |
| No focus visible on custom buttons | `:focus-visible { outline: 2px solid var(--color-primary-500); }` |
| Icon-only buttons without aria-label | Add `aria-label="Close"` to every icon-only button |
| Modal without focus-trap | Use `focus-trap-react` or roll your own |
| Toast without `aria-live` | Add `aria-live="polite"` to toast container |
| Hardcoded `rgb(255,255,255)` in component | Use `var(--color-neutral-0)` |

## Related Skills

- **ui-design-system** — REQUIRED first step, generates the tokens
- **ui-color-system** — Generates accessible color palette
- **ui-dashboard** — Uses these components to compose dashboards
- **web-design-guidelines** — Vercel's UI review checklist for polish

## Part of UI-Factory

This skill is one of the **atoms** in the UI-Factory pattern. Use after `ui-design-system` to generate components, then `ui-dashboard` to compose them into a layout.

Based on the KIMI K2 UI-Factory-Pattern (2026-06-30).
