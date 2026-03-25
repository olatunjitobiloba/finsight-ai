# FinSight AI - Unified Design System

## Overview
Comprehensive theme realignment with consistent colors, spacing, animations, and visual language across all components.

---

## Color Palette

### Brand Colors
- **Primary**: `#00d084` (vibrant emerald green)
- **Primary Dark**: `#00ba77` (darker shade for hover states)
- **Primary Light**: `#00e5a6` (lighter shade for accents)
- **Primary Subtle**: `rgba(0, 208, 132, 0.08)` (low-opacity backgrounds)

### Semantic Colors
- **Success**: `#00d084` (positive actions / green)
- **Warning**: `#fbbf24` (warnings / amber)
- **Error**: `#ef4444` (destructive / red)
- **Info**: `#0c8a55` (informational)
- **Accent**: `#16a34a` (secondary brand, Interswitch)

### Text Colors
- **Primary**: `#0d2818` (main text)
- **Secondary**: `#4a6b5e` (supporting text)
- **Tertiary**: `#6d7d76` (muted text)
- **Inverse**: `#ffffff` (white, on dark backgrounds)

### Background Colors
- **Base**: `#f8fdf9` (main background)
- **Secondary**: `#f0fdf5` (subtle background)
- **Card**: `rgba(255, 255, 255, 0.95)` (elevated surfaces)
- **Input**: `rgba(255, 255, 255, 0.98)` (form inputs)
- **Overlay**: `rgba(13, 40, 24, 0.38)` (modal backdrops)

### Border Colors
- **Default**: `rgba(0, 208, 132, 0.15)` (primary borders)
- **Light**: `rgba(0, 208, 132, 0.08)` (subtle borders)

---

## Spacing System

4px-based modular scale for consistent spacing:

```css
--space-2:   8px    /* 2x base)
--space-3:  12px    /* gaps, small padding)
--space-4:  16px    /* button padding, standard padding)
--space-5:  20px    /* section margins, panel spacing)
--space-6:  24px    /* large padding, headings)
--space-7:  28px    /* very large padding)
--space-8:  32px    /* section gaps)
--space-9:  36px    /* main padding)
```

**Usage Patterns:**
- Gaps between items: `var(--space-2)` to `var(--space-3)`
- Button padding: `var(--space-3) var(--space-4)`
- Card padding: `var(--space-7)` (28px)
- Panel padding: `var(--space-9)` (36px)
- Section margins: `var(--space-6)` (24px)

---

## Typography

### Font Families
- **Primary**: Poppins (UI, body text)
- **Serif**: Newsreader (headline emphasis in dashboard)
- **Mono**: JetBrains Mono, Fira Code (code blocks)
- **Icons**: Font Awesome 6.5.2

### Heading Hierarchy
- H1: `clamp(2rem, 4vw, 2.7rem)` · font-weight: 800 · color: `var(--text-primary)`
- H2: `clamp(1.2rem, 2.4vw, 1.6rem)` · font-weight: 750 · color: `var(--text-primary)`
- H3: varies by section (hero, dashboard)

---

## Shadow System

Three-tier shadow hierarchy for depth:

```css
--shadow-sm:   0 4px 12px rgba(0, 208, 132, 0.08);
--shadow-md:  0 10px 30px rgba(0, 208, 132, 0.12);
--shadow-lg:  0 20px 50px rgba(0, 208, 132, 0.18);
```

**Application:**
- **Small**: hover states, subtle elevation
- **Medium**: cards, panels, default containers
- **Large**: modals, drawers, maximum prominence

---

## Border Radius System

Three consistent sizes:

```css
--radius-sm:   12px  (buttons, inputs, small elements)
--radius-md:   16px  (cards, regular components)
--radius-lg:   24px  (panels, modals, large containers)
```

---

## Animation System

### Duration Variables
```css
--duration-fast:   0.2s   (quick interactions)
--duration-base:   0.3s   (standard transitions)
--duration-slow:   0.5s   (flowing, emphasis)
```

### Easing Functions
```css
--ease-out:      cubic-bezier(0.4, 0, 0.2, 1);
--ease-in-out:   cubic-bezier(0.4, 0, 0.6, 1);
--ease-bounce:   cubic-bezier(0.34, 1.56, 0.64, 1);
```

### Common Animations

#### fadeUp (entrance)
- Used for: Page elements, modal content, list items
- Duration: `var(--duration-base)` (0.3s)
- Transform: `translateY(-16px)` to `translateY(0)`

#### toastIn (toast notifications)
- Duration: `var(--duration-base)` (0.3s)
- Transform: `translate(-50%, 8px)` to `translate(-50%, 0)`

#### spin (loading spinner)
- Duration: `var(--duration-slow)` (0.5s / 900ms for spinner)
- Transform: `rotate(0deg)` to `rotate(360deg)`

#### pulse (critical state)
- Duration: `var(--duration-slow)` (0.5s)
- Opacity: 1 → 0.5 → 1

#### drift-naira (background animation)
- Duration: 35s infinite
- Continuous motion + rotation

#### orbit (brand mark dot)
- Duration: 2.8s infinite
- Square path motion

---

## Component Styling

### Buttons

**Primary Button**
- Background: `var(--primary)` (#00d084)
- Color: `var(--text-inverse)` (white)
- Shadow: `var(--shadow-md)`
- Hover: darker shade + larger shadow
- Padding: `var(--space-3) var(--space-6)` (12px 24px)
- Transition: `var(--duration-fast)` (0.2s)

**Ghost Button**
- Background: `var(--primary-subtle)` (rgba 0.08)
- Border: 1px solid `rgba(0, 208, 132, 0.25)`
- Color: `var(--info)` (#0c8a55)
- Hover: lighter background + visible border

**Danger Button**
- Background: `var(--error)` (#ef4444)
- Color: `var(--text-inverse)` (white)
- Full width by default

**Interswitch Button**
- Background: `var(--accent)` (#16a34a)
- Flex basis: 1 (share container)

### Cards & Panels
- Background: `var(--bg-card)`
- Border: 1px `var(--border)`
- Radius: `var(--radius-lg)` (24px)
- Padding: `var(--space-7)` (28px)
- Shadow: `var(--shadow-md)`
- Backdrop blur: `12px`
- Transition: `var(--duration-base)` (0.3s)
- Hover: border color brightens, shadow increases

### Form Elements

**Text Input / Textarea**
- Border: 2px `var(--border)`
- Background: `var(--bg-input)`
- Color: `var(--text-primary)`
- Focus: border color increases opacity, adds shadow ring
- Radius: `var(--radius-md)` (16px)
- Padding: `var(--space-4)` (16px)

**Select / Dropdown**
- Same as inputs
- Padding: `var(--space-3) var(--space-4)` (12px 16px)

### Tabs
- Border-bottom: 1px `var(--border)`
- Border (tab): 1px `var(--border)`
- Active tab: background `var(--primary)`, color white
- Transition: `var(--duration-fast)` (0.2s)

### Lists & Timeline Items
- Padding: `var(--space-4) var(--space-5)` (16px 20px)
- Border-radius: `var(--radius-md)` (16px)
- Border: 1px `var(--border)`
- Border-left: 5px `var(--primary)` (accent bar)
- Background: `rgba(0, 208, 132, 0.03)`
- Hover: lighter background, increased border, shadow

---

## Responsive Design

### Breakpoints
- Desktop: 1200px+
- Tablet: 700px–1200px
- Mobile: < 700px

### Key Responsive Changes
- Header padding reduced on mobile
- Main padding adjusted: `var(--space-6) var(--space-3) var(--space-9)`
- Buttons full width on mobile
- Tabs stack vertically
- Drawer becomes full viewport width
- Two-column layouts collapse to single column

### Accessibility
- `prefers-reduced-motion: reduce` disables all animations
- All interactive elements have visible focus states
- Color contrast ratios meet WCAG AA standards

---

## Cleo Mode (Alternative Theme)

Warm, earthy dashboard variant:

```css
--bg-primary:      #f8f4ee (warm beige)
--bg-secondary:    #efe2d2 (softer beige)
--text-primary:    #2a130f (dark brown)
--text-secondary:  #6d4d40 (warm brown)
--primary:         #2f9e6f (forest green)
--warning:         #db9f44 (warm amber)
--error:           #b8392f (clay red)
```

### Key Cleo Differences
- Color palette shifted to earth tones
- Typography: Sora (sans-serif) primary
- Background: gradient with warm radial overlays
- Brand mark dot: #e98e4a (warm gold)
- Header tagline color: darker, earthy

---

## Best Practices

### Color Usage
1. Use semantic variables (`--success`, `--error`) over hard-coded colors
2. Always use `var(--text-primary)` for main text
3. Use `var(--primary)` for brand actions
4. Use opacity scales for subtle variations: `.08`, `.12`, `.15`, `.2`, etc.

### Spacing
1. Always use spacing variables from `--space-2` to `--space-9`
2. Combine values for custom spacing: `var(--space-4) var(--space-6)` for padding
3. Use consistent gaps in flex/grid layouts: `gap: var(--space-3)`

### Animation
1. Use predefined animation durations: `fast`, `base`, `slow`
2. Apply easing functions for purposeful motion
3. Keep animations under 0.5s for UI interactions
4. Longer durations (2s+) for background/ambient animations

### Shadows
1. Use small shadows for subtle hover effects
2. Medium shadows for standard cards/panels
3. Large shadows only for modals/overlays
4. Never stack multiple shadows; use one appropriate level

---

## Migration Notes

### Old → New Variable Mappings
| Old | New |
|-----|-----|
| `--text` | `var(--text-primary)` |
| `--text-sub` | `var(--text-secondary)` |
| `--blue` | `var(--primary)` |
| `--green` | `var(--success)` |
| `--yellow` | `var(--warning)` |
| `--orange` | `var(--warning)` |
| `--red` | `var(--error)` |
| `--radius` | `var(--radius-md)` |
| `--shadow` | `var(--shadow-md)` |
| `--blur` | `var(--glass-blur)` |

### Timing Consolidation
Previously 7+ different timing values (0.2s, 0.22s, 0.26s, 0.28s, 0.3s, etc.) 
→ Now 3 standardized durations: `fast`, `base`, `slow`

---

## Testing Checklist

- [ ] All text uses `--text-primary` / `--text-secondary`
- [ ] All brand colors use `var(--primary)` family
- [ ] All spacing uses `--space-*` variables
- [ ] All shadows use `--shadow-*` levels
- [ ] All border radiuses use `--radius-*` scales
- [ ] All animations use `--duration-*` + `--ease-*`
- [ ] Mobile responsive behaviors tested
- [ ] Reduced motion preference respected
- [ ] Color contrast verified (WCAG AA)
- [ ] Cleo mode theme variables applied

---

## Future Enhancements

1. **Dark Mode**: Add complementary dark palette variables
2. **Accessibility**: Expand contrast ratio testing automation
3. **Component Library**: Build isolated component showcase
4. **Animation Library**: Expand motion effects catalog
5. **Theming API**: Allow runtime theme switching
