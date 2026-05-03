---
name: Lotus Travel Experience
colors:
  surface: '#fbf9f8'
  surface-dim: '#dbd9d9'
  surface-bright: '#fbf9f8'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f5f3f3'
  surface-container: '#efeded'
  surface-container-high: '#eae8e7'
  surface-container-highest: '#e4e2e2'
  on-surface: '#1b1c1c'
  on-surface-variant: '#4d4447'
  inverse-surface: '#303030'
  inverse-on-surface: '#f2f0f0'
  outline: '#7f7477'
  outline-variant: '#d0c3c6'
  surface-tint: '#6b5a5f'
  primary: '#6b5a5f'
  on-primary: '#ffffff'
  primary-container: '#f8e1e7'
  on-primary-container: '#746368'
  inverse-primary: '#d7c1c7'
  secondary: '#735c00'
  on-secondary: '#ffffff'
  secondary-container: '#fed65b'
  on-secondary-container: '#745c00'
  tertiary: '#5e5e5f'
  on-tertiary: '#ffffff'
  tertiary-container: '#e8e6e6'
  on-tertiary-container: '#676767'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#f4dde3'
  primary-fixed-dim: '#d7c1c7'
  on-primary-fixed: '#24181c'
  on-primary-fixed-variant: '#524348'
  secondary-fixed: '#ffe088'
  secondary-fixed-dim: '#e9c349'
  on-secondary-fixed: '#241a00'
  on-secondary-fixed-variant: '#574500'
  tertiary-fixed: '#e4e2e2'
  tertiary-fixed-dim: '#c7c6c6'
  on-tertiary-fixed: '#1b1c1c'
  on-tertiary-fixed-variant: '#464747'
  background: '#fbf9f8'
  on-background: '#1b1c1c'
  surface-variant: '#e4e2e2'
typography:
  headline-lg:
    fontFamily: Noto Serif
    fontSize: 40px
    fontWeight: '600'
    lineHeight: '1.2'
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Noto Serif
    fontSize: 28px
    fontWeight: '500'
    lineHeight: '1.3'
  body-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 18px
    fontWeight: '400'
    lineHeight: '1.6'
  body-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.5'
  label-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 12px
    fontWeight: '600'
    lineHeight: '1.0'
    letterSpacing: 0.05em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 8px
  xs: 4px
  sm: 12px
  md: 24px
  lg: 48px
  xl: 80px
  gutter: 24px
  margin-mobile: 16px
  margin-desktop: 64px
---

## Brand & Style

The design system is rooted in the "Lotus" philosophy—representing purity, resilience, and a graceful journey. It targets premium travelers who value serenity and efficiency within the high-velocity environment of an airport. The brand personality is welcoming, sophisticated, and ethereal, aiming to reduce travel anxiety through visual lightness.

The aesthetic blends **Minimalism** with **Glassmorphism**. By prioritizing expansive whitespace and translucent layers, the UI mimics the delicate petals of a lotus floating on water. The visual hierarchy is intentionally "lightweight," avoiding heavy blocks of color in favor of soft gradients and subtle gold accents that guide the eye without overwhelming the senses.

## Colors

The color palette is inspired by the transition of light on a blooming lotus. 
- **Primary:** A soft, petal pink (#F8E1E7) used for primary interactive states and highlight backgrounds.
- **Secondary:** A refined metallic gold (#D4AF37) reserved for premium cues, iconography, and subtle accents to denote luxury and Adani’s excellence.
- **Tertiary/Surface:** An off-white "Cloud" (#FDFBFB) that serves as the base canvas, providing more warmth than a clinical pure white.
- **Neutral:** A deep charcoal grey (#4A4A4A) ensures high readability while maintaining a softer contrast than pure black.

## Typography

This design system utilizes a sophisticated pairing of fonts. **Noto Serif** is used for major headlines to provide an elegant, literary feel that aligns with the premium Adani brand. **Plus Jakarta Sans** is the workhorse font, chosen for its friendly, modern, and highly legible geometric forms, making it ideal for flight data and navigation on small screens.

To maintain the "lightweight" feel, typography relies on generous line heights and tracking. Labels are often capitalized with increased letter spacing to create a sense of order and professional clarity.

## Layout & Spacing

The layout follows a **Fluid Grid** model with an emphasis on "Airy" negative space. On desktop, the system utilizes a 12-column grid with wide margins (64px) to center the content and provide a sense of focus. On mobile, the system transitions to a 4-column grid with 16px margins.

Spacing is governed by an 8px baseline rhythm. To achieve the "Lotus" inspired lightness, vertical spacing between sections (XL) is intentionally larger than industry standards, allowing each piece of information to breathe and preventing a cluttered, "hectic airport" feeling.

## Elevation & Depth

Depth is achieved through **Glassmorphism** and **Ambient Shadows**. Instead of solid dividers, the design system uses varying levels of background blur (10px to 20px) on semi-transparent white surfaces (Alpha 60-80%).

Shadows are extremely diffused, using a hint of the primary pink or gold in the shadow color to avoid "dirty" grey blurs.
- **Level 1 (Flight Cards):** Subtle 15% opacity pink-tinted shadow with a 20px blur.
- **Level 2 (Dropdowns/Modals):** Glassmorphic surface with a gold-tinted 10% shadow and a 1px solid white border at 30% opacity to define the edge.

## Shapes

The shape language is organic and soft, mimicking the curvature of a lotus petal. Sharp corners are avoided entirely. 
- **Buttons and Chips:** Use a pill-shaped radius (rounded-xl) to feel approachable and smooth.
- **Cards and Containers:** Use a large 1.5rem (24px) radius to soften the layout.
- **Inputs:** Use a 1rem (16px) radius, providing a modern but structured look.

## Components

### Flight Cards
Designed as glassmorphic "petals." They feature a subtle horizontal gradient background. Flight numbers and times are prominent, while secondary info (gate, terminal) is rendered in small-caps `label-sm` typography. Status indicators (On Time, Delayed) use a soft glow effect rather than high-contrast solid colors.

### Search Inputs
The primary search bar is an oversized, pill-shaped element. It uses a 1px Gold border in focus state and includes a soft-glow shadow. Icons are thin-stroke (1.5pt) to maintain the lightweight visual hierarchy.

### Navigational Elements
- **Desktop:** A top-fixed frosted glass bar with gold underlines for active states.
- **Mobile:** A floating bottom navigation dock with a high blur radius, ensuring the content behind it is visible but not distracting.

### Primary Buttons
Pill-shaped with a soft gradient from White to Primary Pink. The text is Gold or Charcoal Grey. No heavy drop shadows; instead, they use a "lifting" effect on hover where the background blur increases.

### Progress Indicators
For check-in or booking flows, use thin, organic lines with gold dots, avoiding bulky progress bars to maintain the airy aesthetic.