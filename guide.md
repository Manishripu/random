# Angular 19 — Complete Guide: Generate, Share & Consume CSS as a Library Component

-----

## Table of Contents

1. [Overview & Architecture](#1-overview--architecture)
1. [Setting Up the Workspace](#2-setting-up-the-workspace)
1. [Generating the CSS Library](#3-generating-the-css-library)
1. [Structuring Styles Inside the Library](#4-structuring-styles-inside-the-library)
1. [Exposing Styles — All Methods](#5-exposing-styles--all-methods)
1. [Building the Library](#6-building-the-library)
1. [Sharing the Library — Option A: npm Registry](#7-sharing-the-library--option-a-npm-registry)
1. [Sharing the Library — Option B: Git-based Install](#8-sharing-the-library--option-b-git-based-install)
1. [Sharing the Library — Option C: npm link (Local Dev)](#9-sharing-the-library--option-c-npm-link-local-dev)
1. [Consuming the Library in Another App](#10-consuming-the-library-in-another-app)
1. [Versioning & Release Strategy](#11-versioning--release-strategy)
1. [CI/CD Pipeline](#12-cicd-pipeline)
1. [Common Pitfalls & Best Practices](#13-common-pitfalls--best-practices)

-----

## 1. Overview & Architecture

The goal is to create a single Angular library (`ui-kit`) that holds all shared CSS — design tokens, mixins, component styles — and distribute it so multiple Angular apps can consume it consistently.

```
┌─────────────────────────────────────────────────────────────┐
│                    ui-kit (library repo)                    │
│                                                             │
│  projects/ui-kit/src/                                       │
│    styles/                                                  │
│      _tokens.scss      ← CSS custom properties             │
│      _mixins.scss      ← reusable SCSS mixins              │
│      _typography.scss  ← font rules                        │
│      theme.css         ← pre-compiled global theme         │
│    lib/                                                     │
│      button/           ← component with scoped styles      │
│      card/             ← component with scoped styles      │
│    public-api.ts       ← barrel export                     │
└──────────────────────────┬──────────────────────────────────┘
                           │
            ┌──────────────┼──────────────┐
            │              │              │
     npm registry       git tag       npm link
            │              │              │
   ┌────────▼───┐  ┌───────▼────┐  ┌────▼───────┐
   │   app-one  │  │   app-two  │  │ local-app  │
   │ (repo-b)   │  │ (repo-c)   │  │  (dev)     │
   └────────────┘  └────────────┘  └────────────┘
```

-----

## 2. Setting Up the Workspace

### Create the Angular workspace (library repo)

```bash
# Create a workspace without a default app
ng new ui-kit-workspace --no-create-application --style scss
cd ui-kit-workspace
```

Your `angular.json` will be empty of projects initially. This is intentional — the workspace is purely a library host.

-----

## 3. Generating the CSS Library

```bash
ng generate library ui-kit --prefix=ui
```

This creates:

```
projects/
  ui-kit/
    src/
      lib/
        ui-kit.component.ts       ← sample component (delete or keep)
        ui-kit.module.ts          ← NgModule (optional in Angular 19)
      public-api.ts               ← what consumers can import
    ng-package.json               ← ng-packagr config
    package.json                  ← library's own package.json
    tsconfig.lib.json
    tsconfig.spec.json
```

### Update `projects/ui-kit/package.json`

```json
{
  "name": "@your-org/ui-kit",
  "version": "1.0.0",
  "peerDependencies": {
    "@angular/core": ">=19.0.0",
    "@angular/common": ">=19.0.0"
  },
  "scripts": {
    "prepare": "ng build ui-kit"
  }
}
```

> **Why peerDependencies?** Declaring Angular as a peer dep (not a direct dep) prevents version conflicts in consuming apps. The app itself provides Angular — the library just says “I need at least version 19”.

-----

## 4. Structuring Styles Inside the Library

Create a clean folder structure for all shared styles:

```bash
mkdir -p projects/ui-kit/src/styles
```

```
projects/ui-kit/src/styles/
  _tokens.scss        ← CSS custom properties (design tokens)
  _mixins.scss        ← SCSS mixins
  _typography.scss    ← font/text utilities
  _reset.scss         ← optional CSS reset
  index.scss          ← barrel — imports all partials
  theme.css           ← pre-compiled output for non-SCSS consumers
```

### `_tokens.scss` — Design Tokens

```scss
// projects/ui-kit/src/styles/_tokens.scss

:root {
  // Colors
  --ui-primary:        #3f51b5;
  --ui-primary-dark:   #283593;
  --ui-primary-light:  #c5cae9;
  --ui-accent:         #ff4081;
  --ui-warn:           #f44336;
  --ui-success:        #4caf50;

  // Neutrals
  --ui-bg:             #ffffff;
  --ui-surface:        #f5f5f5;
  --ui-text:           #212121;
  --ui-text-secondary: #757575;
  --ui-border:         #e0e0e0;

  // Spacing scale
  --ui-space-xs:  4px;
  --ui-space-sm:  8px;
  --ui-space-md:  16px;
  --ui-space-lg:  24px;
  --ui-space-xl:  32px;
  --ui-space-2xl: 48px;

  // Typography
  --ui-font-family: 'Inter', 'Roboto', sans-serif;
  --ui-font-size-sm:   12px;
  --ui-font-size-base: 14px;
  --ui-font-size-md:   16px;
  --ui-font-size-lg:   20px;
  --ui-font-size-xl:   24px;

  // Shape
  --ui-radius-sm: 4px;
  --ui-radius-md: 8px;
  --ui-radius-lg: 16px;
  --ui-radius-full: 9999px;

  // Elevation / Shadow
  --ui-shadow-sm: 0 1px 3px rgba(0,0,0,.12);
  --ui-shadow-md: 0 4px 6px rgba(0,0,0,.12);
  --ui-shadow-lg: 0 10px 20px rgba(0,0,0,.15);

  // Transitions
  --ui-transition: 200ms ease;
}
```

### `_mixins.scss` — Reusable Mixins

```scss
// projects/ui-kit/src/styles/_mixins.scss

// Flexbox helpers
@mixin flex-center {
  display: flex;
  align-items: center;
  justify-content: center;
}

@mixin flex-between {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

// Card base style
@mixin card-base($padding: var(--ui-space-md)) {
  background: var(--ui-bg);
  border-radius: var(--ui-radius-md);
  box-shadow: var(--ui-shadow-sm);
  padding: $padding;
  border: 1px solid var(--ui-border);
}

// Button base
@mixin button-base {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--ui-space-sm);
  padding: var(--ui-space-sm) var(--ui-space-md);
  border-radius: var(--ui-radius-sm);
  font-family: var(--ui-font-family);
  font-size: var(--ui-font-size-base);
  cursor: pointer;
  transition: all var(--ui-transition);
  border: none;
  outline: none;

  &:focus-visible {
    outline: 2px solid var(--ui-primary);
    outline-offset: 2px;
  }
}

// Responsive breakpoints
@mixin breakpoint($bp) {
  $breakpoints: (
    'sm': 576px,
    'md': 768px,
    'lg': 992px,
    'xl': 1200px
  );

  @if map-has-key($breakpoints, $bp) {
    @media (min-width: map-get($breakpoints, $bp)) {
      @content;
    }
  }
}

// Truncate text
@mixin truncate($lines: 1) {
  @if $lines == 1 {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  } @else {
    display: -webkit-box;
    -webkit-line-clamp: $lines;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
}

// Visually hidden (accessible)
@mixin visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
```

### `_typography.scss` — Typography Utilities

```scss
// projects/ui-kit/src/styles/_typography.scss

.ui-text-sm   { font-size: var(--ui-font-size-sm); }
.ui-text-base { font-size: var(--ui-font-size-base); }
.ui-text-md   { font-size: var(--ui-font-size-md); }
.ui-text-lg   { font-size: var(--ui-font-size-lg); }
.ui-text-xl   { font-size: var(--ui-font-size-xl); }

.ui-font-bold   { font-weight: 700; }
.ui-font-medium { font-weight: 500; }
.ui-font-normal { font-weight: 400; }

.ui-text-primary   { color: var(--ui-primary); }
.ui-text-secondary { color: var(--ui-text-secondary); }
.ui-text-warn      { color: var(--ui-warn); }
.ui-text-success   { color: var(--ui-success); }
```

### `index.scss` — Barrel File

```scss
// projects/ui-kit/src/styles/index.scss
@forward 'tokens';
@forward 'mixins';
@forward 'typography';
@forward 'reset';
```

-----

## 5. Exposing Styles — All Methods

### Method A: Component-scoped Styles (Automatic)

Each component in the library carries its own encapsulated styles. Consumers get them automatically just by using the component.

```typescript
// projects/ui-kit/src/lib/button/button.component.ts
import { Component, Input } from '@angular/core';

@Component({
  selector: 'ui-button',
  standalone: true,
  template: `
    <button [class]="'ui-btn ui-btn--' + variant" [disabled]="disabled">
      <ng-content />
    </button>
  `,
  styleUrl: './button.component.scss'
})
export class ButtonComponent {
  @Input() variant: 'primary' | 'secondary' | 'ghost' = 'primary';
  @Input() disabled = false;
}
```

```scss
// projects/ui-kit/src/lib/button/button.component.scss
@use '../../styles/mixins' as m;

.ui-btn {
  @include m.button-base();

  &--primary {
    background: var(--ui-primary);
    color: white;

    &:hover:not(:disabled) {
      background: var(--ui-primary-dark);
    }
  }

  &--secondary {
    background: transparent;
    color: var(--ui-primary);
    border: 1px solid var(--ui-primary);

    &:hover:not(:disabled) {
      background: var(--ui-primary-light);
    }
  }

  &--ghost {
    background: transparent;
    color: var(--ui-text);

    &:hover:not(:disabled) {
      background: var(--ui-surface);
    }
  }

  &:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }
}
```

### Method B: Expose Global Stylesheet via `ng-package.json`

Declare style assets so consumers can reference the pre-built theme CSS:

```json
// projects/ui-kit/ng-package.json
{
  "$schema": "../../node_modules/ng-packagr/ng-package.schema.json",
  "lib": {
    "entryFile": "src/public-api.ts",
    "styleIncludePaths": ["src"]
  },
  "assets": [
    "./src/styles/**/*.scss",
    "./src/styles/theme.css"
  ]
}
```

After building, the `dist/ui-kit/` will contain a `styles/` folder that consumers can reference.

### Method C: Expose SCSS Partials for `@use`

The SCSS partials in `src/styles/` are copied to `dist/ui-kit/styles/` via the `assets` declaration above. Consumers can then:

```scss
// in any consuming app component
@use '@your-org/ui-kit/styles/mixins' as m;

.my-card {
  @include m.card-base();
}
```

### Method D: Pre-compile a `theme.css`

For teams who don’t use SCSS, compile a ready-to-use CSS file:

```bash
# Build theme.css from index.scss using sass CLI
npx sass projects/ui-kit/src/styles/index.scss \
           projects/ui-kit/src/styles/theme.css \
           --no-source-map
```

Add this to your build script in `package.json`:

```json
{
  "scripts": {
    "build:theme": "sass projects/ui-kit/src/styles/index.scss projects/ui-kit/src/styles/theme.css --no-source-map",
    "build:lib": "npm run build:theme && ng build ui-kit"
  }
}
```

### Update `public-api.ts`

```typescript
// projects/ui-kit/src/public-api.ts

// Export all components
export * from './lib/button/button.component';
export * from './lib/card/card.component';

// Note: SCSS styles are exposed via assets (ng-package.json),
// not via TypeScript exports. No need to export style files here.
```

-----

## 6. Building the Library

```bash
# Standard build
ng build ui-kit

# Watch mode (for local development)
ng build ui-kit --watch
```

The output lands in:

```
dist/
  ui-kit/
    esm2022/            ← ES module output
    fesm2022/           ← Flattened ES modules
    styles/
      _tokens.scss      ← SCSS partials (copied via assets)
      _mixins.scss
      _typography.scss
      index.scss
      theme.css         ← Pre-compiled CSS
    package.json
    public-api.d.ts
    README.md
```

-----

## 7. Sharing the Library — Option A: npm Registry

### A1. Public npm

```bash
cd dist/ui-kit

# First time — login
npm login

# Publish publicly
npm publish --access public
```

Consumers install it like any package:

```bash
npm install @your-org/ui-kit
```

### A2. Private Registry — GitHub Packages

**In the library repo**, create `.npmrc`:

```
@your-org:registry=https://npm.pkg.github.com
//npm.pkg.github.com/:_authToken=${GITHUB_TOKEN}
```

Publish:

```bash
cd dist/ui-kit
npm publish
```

**In each consuming repo**, add the same `.npmrc`:

```
@your-org:registry=https://npm.pkg.github.com
//npm.pkg.github.com/:_authToken=${GITHUB_TOKEN}
```

Then install normally:

```bash
npm install @your-org/ui-kit@1.0.0
```

### A3. Self-hosted — Verdaccio

Verdaccio is a free, lightweight private npm registry you can self-host.

```bash
# Run Verdaccio (Docker)
docker run -d -p 4873:4873 verdaccio/verdaccio

# Point to it
npm set registry http://localhost:4873

# Publish
cd dist/ui-kit
npm publish
```

-----

## 8. Sharing the Library — Option B: Git-based Install

No registry needed. npm clones the git repo and installs from source.

### Step 1 — Commit `dist/` to the library repo

```bash
# Remove dist/ from .gitignore
echo "!dist/" >> .gitignore

# Build
ng build ui-kit

# Commit the build output
git add dist/
git commit -m "build: v1.0.0"
git tag v1.0.0
git push origin main --tags
```

### Step 2 — Install in consuming repo

```bash
# By tag (recommended)
npm install git+https://github.com/your-org/ui-kit.git#v1.0.0

# By commit SHA (most locked-down)
npm install git+https://github.com/your-org/ui-kit.git#a3f8c1d

# Shorthand GitHub syntax
npm install your-org/ui-kit#v1.0.0

# With semver range over tags
npm install "your-org/ui-kit#semver:^1.0.0"
```

This is what goes into `package.json`:

```json
{
  "dependencies": {
    "@your-org/ui-kit": "git+https://github.com/your-org/ui-kit.git#v1.0.0"
  }
}
```

### How `package-lock.json` tracks it

npm locks the exact commit SHA, not the tag name:

```json
{
  "dependencies": {
    "@your-org/ui-kit": {
      "version": "1.0.0",
      "resolved": "git+https://github.com/your-org/ui-kit.git#a3f8c1d2e4b5f6...",
      "from": "git+https://github.com/your-org/ui-kit.git#v1.0.0"
    }
  }
}
```

This guarantees `npm ci` always installs the exact same code in CI pipelines.

### Authentication for Private Repos

**SSH (developer machines):**

```bash
npm install git+ssh://git@github.com/your-org/ui-kit.git#v1.0.0
```

**HTTPS with token (CI pipelines):**

```bash
# In CI environment variables: GITHUB_TOKEN=ghp_xxxx
git config --global \
  url."https://${GITHUB_TOKEN}@github.com/".insteadOf \
  "https://github.com/"

npm install
```

### Alternative: `prepare` Script (build on install)

Instead of committing `dist/`, trigger the build automatically during `npm install`:

```json
// projects/ui-kit/package.json
{
  "scripts": {
    "prepare": "ng build ui-kit"
  }
}
```

> ⚠️ This makes `npm install` significantly slower in consuming repos and requires Angular CLI and compatible Node.js on every machine. **Committing dist/ is usually preferable** for git-based installs.

-----

## 9. Sharing the Library — Option C: npm link (Local Dev)

Use this when developing the library and a consuming app at the same time.

### Terminal 1 — Library repo

```bash
# Build in watch mode so changes rebuild automatically
ng build ui-kit --watch

# In a second terminal, register the dist as a global symlink
cd dist/ui-kit
npm link
```

### Terminal 2 — Consuming repo

```bash
# Create a symlink in node_modules pointing to the dist folder
npm link @your-org/ui-kit

# Start the app — it picks up library changes live
ng serve
```

### What the symlink chain looks like

```
consuming-app/node_modules/@your-org/ui-kit
        │ (symlink)
        └──► ~/.nvm/versions/node/v22/lib/node_modules/@your-org/ui-kit
                    │ (symlink)
                    └──► ~/projects/ui-kit/dist/ui-kit
```

Every time the library rebuilds (triggered by `--watch`), the consuming app hot-reloads with the latest styles.

### Clean up when done

```bash
# In consuming repo
npm unlink @your-org/ui-kit

# In library dist/
npm unlink
```

-----

## 10. Consuming the Library in Another App

Regardless of which sharing method was used, consumption is identical.

### Step 1 — Install

```bash
npm install @your-org/ui-kit
```

### Step 2 — Configure SCSS path resolution

In `angular.json` of the consuming app:

```json
{
  "projects": {
    "my-app": {
      "architect": {
        "build": {
          "options": {
            "stylePreprocessorOptions": {
              "includePaths": ["node_modules"]
            }
          }
        }
      }
    }
  }
}
```

This allows `@use '@your-org/ui-kit/styles/...'` to resolve correctly.

### Step 3A — Use pre-compiled global theme (simplest)

In `angular.json` styles array:

```json
{
  "styles": [
    "node_modules/@your-org/ui-kit/styles/theme.css",
    "src/styles.scss"
  ]
}
```

Or in your own `src/styles.scss`:

```scss
@import '@your-org/ui-kit/styles/theme.css';
```

### Step 3B — Use SCSS partials selectively

In any component’s `.scss` file:

```scss
// Import only what you need
@use '@your-org/ui-kit/styles/tokens';
@use '@your-org/ui-kit/styles/mixins' as m;

.my-dashboard-card {
  @include m.card-base(var(--ui-space-lg));
  background: var(--ui-surface);
}

.my-page-title {
  font-size: var(--ui-font-size-xl);
  color: var(--ui-primary);
  font-family: var(--ui-font-family);
}
```

### Step 4 — Use library components

```typescript
// app.component.ts
import { Component } from '@angular/core';
import { ButtonComponent, CardComponent } from '@your-org/ui-kit';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [ButtonComponent, CardComponent],
  template: `
    <ui-card>
      <h2>Hello from ui-kit</h2>
      <ui-button variant="primary" (click)="handleClick()">
        Submit
      </ui-button>
      <ui-button variant="ghost">
        Cancel
      </ui-button>
    </ui-card>
  `
})
export class AppComponent {
  handleClick() { console.log('clicked'); }
}
```

Component styles are bundled with the component — no extra import needed.

### Consuming CSS Custom Properties in Templates

Since CSS tokens are global (applied to `:root`), they work anywhere:

```html
<!-- Inline style using library tokens -->
<div style="color: var(--ui-primary); padding: var(--ui-space-md)">
  This uses ui-kit tokens directly in HTML
</div>
```

```scss
// Or in a local component stylesheet with no library import needed
.my-component {
  color: var(--ui-text);
  border-radius: var(--ui-radius-md);
  transition: all var(--ui-transition);
}
```

-----

## 11. Versioning & Release Strategy

### Semantic Versioning (SemVer)

```
MAJOR . MINOR . PATCH
  2   .   1   .   3

PATCH (2.1.3 → 2.1.4): Bug fixes, no breaking changes
MINOR (2.1.3 → 2.2.0): New tokens/mixins added, backwards compatible
MAJOR (2.1.3 → 3.0.0): Renamed tokens, removed classes — BREAKING
```

### What counts as a breaking CSS change?

|Change                      |Version bump  |
|----------------------------|--------------|
|Rename a CSS custom property|**MAJOR**     |
|Remove a mixin              |**MAJOR**     |
|Remove a utility class      |**MAJOR**     |
|Change a mixin’s signature  |**MAJOR**     |
|Add a new token             |MINOR         |
|Add a new mixin             |MINOR         |
|Change a token’s value      |PATCH or MINOR|
|Bug fix in a component style|PATCH         |

### Release workflow

```bash
# 1. Make changes, build, test
ng build ui-kit

# 2. Bump version
npm version patch   # 1.0.0 → 1.0.1
npm version minor   # 1.0.0 → 1.1.0
npm version major   # 1.0.0 → 2.0.0

# This auto-creates a git tag (e.g., v1.1.0)

# 3. Push with tags
git push origin main --tags

# 4. Publish
cd dist/ui-kit
npm publish

# 5. Beta / canary release
npm publish --tag beta
# Consumers opt in explicitly:
# npm install @your-org/ui-kit@beta
```

-----

## 12. CI/CD Pipeline

### Library repo (GitHub Actions)

```yaml
# .github/workflows/publish.yml
name: Build & Publish UI Kit

on:
  push:
    tags:
      - 'v*'

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: '22'
          registry-url: 'https://npm.pkg.github.com'

      - name: Install dependencies
        run: npm ci

      - name: Build library
        run: ng build ui-kit

      - name: Publish to GitHub Packages
        run: |
          cd dist/ui-kit
          npm publish
        env:
          NODE_AUTH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### Consuming app repo

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: '22'
          registry-url: 'https://npm.pkg.github.com'

      - name: Configure npm auth
        run: echo "//npm.pkg.github.com/:_authToken=${{ secrets.GITHUB_TOKEN }}" >> ~/.npmrc

      - name: Install
        run: npm ci

      - name: Build
        run: ng build --configuration production
```

-----

## 13. Common Pitfalls & Best Practices

### Pitfall 1: SCSS partials not found in dist

**Problem:** Consumer gets `Can't find stylesheet to import` when using `@use '@your-org/ui-kit/styles/...'`.

**Fix:** Ensure `ng-package.json` has the assets block AND `angular.json` of the consuming app has `stylePreprocessorOptions.includePaths: ["node_modules"]`.

-----

### Pitfall 2: CSS custom properties not applying

**Problem:** Components use `var(--ui-primary)` but the color doesn’t show.

**Fix:** The `:root` block from `_tokens.scss` must be included globally. Either import `theme.css` in `angular.json` styles array, or include it in the consuming app’s root `styles.scss`.

-----

### Pitfall 3: Styles leaking between components

**Problem:** A style defined in one library component affects elements outside it.

**Fix:** Never use `ViewEncapsulation.None` in library components unless intentional. Keep the default `Emulated` encapsulation.

-----

### Pitfall 4: `ng-deep` usage in library components

**Problem:** Using `::ng-deep` in a library component leaks styles to the entire consuming app.

**Fix:** Avoid `::ng-deep` in library components entirely. Expose customization through CSS custom properties instead:

```scss
// ✅ Good — consumer can override via CSS variable
.ui-button {
  background: var(--ui-button-bg, var(--ui-primary));
}

// Consumer overrides per component:
// ui-button { --ui-button-bg: hotpink; }
```

-----

### Pitfall 5: Breaking changes without major version bump

**Problem:** A token is renamed from `--ui-color-brand` to `--ui-primary` and consuming apps silently break (styles just disappear).

**Fix:** Keep old tokens as aliases during a deprecation period:

```scss
:root {
  --ui-primary: #3f51b5;
  --ui-color-brand: var(--ui-primary); // deprecated alias — remove in v3
}
```

-----

### Best Practice Summary

|Practice                                       |Why                                      |
|-----------------------------------------------|-----------------------------------------|
|Use CSS custom properties for all design tokens|Consumers can override without SCSS      |
|Ship both raw SCSS and compiled CSS            |Serves both SCSS and non-SCSS consumers  |
|Use `peerDependencies` for Angular             |Avoids version conflicts in host apps    |
|Treat CSS renames as breaking changes          |Prevents silent style failures           |
|Keep one mixin/concept per partial file        |Makes selective imports possible         |
|Never use `!important` in library styles       |Consumers can’t override it easily       |
|Document all exposed tokens                    |Consumers need to know what’s available  |
|Add `stylePreprocessorOptions` to docs         |Easy to miss, causes hard-to-debug errors|

```

```