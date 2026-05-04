# Angular Global CSS Library — Build, Publish & Consume

> A complete, production-ready guide to building a shared SCSS/CSS design system library (design tokens, component styles, typography, themes) in Angular 19 using ng-packagr, publishing via Jenkins + S3 + CloudFront, and consuming globally and at component level in other Angular repos.

-----

## Table of Contents

1. [Architecture Overview](#architecture-overview)
1. [Prerequisites](#prerequisites)
1. [Phase 1 — Structure the CSS Library (Repo A)](#phase-1--structure-the-css-library-repo-a)
1. [Phase 2 — Author the SCSS](#phase-2--author-the-scss)
1. [Phase 3 — Configure ng-packagr for CSS Output](#phase-3--configure-ng-packagr-for-css-output)
1. [Phase 4 — Build & Verify](#phase-4--build--verify)
1. [Phase 5 — Package & Publish via Jenkins → S3](#phase-5--package--publish-via-jenkins--s3)
1. [Phase 6 — Serve via CloudFront](#phase-6--serve-via-cloudfront)
1. [Phase 7 — Consume in Repo B (Global Level)](#phase-7--consume-in-repo-b-global-level)
1. [Phase 8 — Consume in Repo B (Component Level)](#phase-8--consume-in-repo-b-component-level)
1. [Phase 9 — Theming (Dark / Light Mode)](#phase-9--theming-dark--light-mode)
1. [Phase 10 — Updating the Library](#phase-10--updating-the-library)
1. [Best Practices](#best-practices)
1. [Common Mistakes](#common-mistakes)
1. [Limitations & Mitigations](#limitations--mitigations)
1. [Quick Reference Cheatsheet](#quick-reference-cheatsheet)

-----

## Architecture Overview

```
Repo A — Angular Workspace (CSS Library)
  └── projects/design-system/
        └── src/
              ├── tokens/          ← CSS custom properties
              ├── typography/      ← Font scale, line-height, weights
              ├── components/      ← Button, card, input styles
              ├── themes/          ← Light / dark theme overrides
              └── index.scss       ← Master entry point
                    ↓
        ng build design-system     ← ng-packagr compiles SCSS → CSS
                    ↓
        dist/design-system/
              ├── _index.scss      ← Importable SCSS (for component-level use)
              ├── design-system.css← Precompiled CSS (for global use)
              └── package.json
                    ↓
        npm pack dist/design-system
                    ↓
        your-org-design-system-1.0.0.tgz
                    ↓
Jenkins Pipeline
  └── aws s3 cp → s3://your-bucket/design-system/1.0.0/
                    ↓
CloudFront CDN
  └── https://cdn.your-org.com/design-system/1.0.0/*.tgz
                    ↓
Repo B — Consumer Angular App
  ├── Global:    styles.scss        @use '@your-org/design-system'
  └── Component: button.component.scss  @use '@your-org/design-system/tokens' as *
```

-----

## Prerequisites

|Tool              |Minimum Version|Check           |
|------------------|---------------|----------------|
|Node.js           |18+            |`node --version`|
|npm               |9+             |`npm --version` |
|Angular CLI       |19+            |`ng version`    |
|Sass (via Angular)|bundled        |—               |
|AWS CLI           |v2             |`aws --version` |

-----

## Phase 1 — Structure the CSS Library (Repo A)

### 1.1 — Generate the Workspace & Library

```bash
ng new repo-a --no-create-application
cd repo-a
ng generate library design-system
```

### 1.2 — Full Folder Structure

Delete the default generated component/service/module files — this is a CSS-only library. Replace with:

```
projects/design-system/
├── package.json                  ← Library metadata & version
├── ng-package.json               ← ng-packagr config
├── tsconfig.lib.json
└── src/
    ├── index.scss                ← ✅ Master entry — imports everything
    ├── public-api.ts             ← Minimal (re-exports scss paths for ng-packagr)
    │
    ├── tokens/
    │   ├── _colors.scss          ← Color palette as CSS variables
    │   ├── _spacing.scss         ← Spacing scale
    │   ├── _elevation.scss       ← Box shadows
    │   ├── _breakpoints.scss     ← Responsive breakpoints
    │   └── _index.scss           ← Barrel: forwards all tokens
    │
    ├── typography/
    │   ├── _scale.scss           ← Font sizes (h1–h6, body, caption)
    │   ├── _weights.scss         ← Font weight definitions
    │   ├── _lineheight.scss      ← Line height scale
    │   ├── _fonts.scss           ← @font-face declarations
    │   └── _index.scss
    │
    ├── components/
    │   ├── _button.scss          ← Button variants
    │   ├── _card.scss            ← Card styles
    │   ├── _input.scss           ← Form input styles
    │   ├── _badge.scss
    │   └── _index.scss
    │
    └── themes/
        ├── _light.scss           ← Light theme variable overrides
        ├── _dark.scss            ← Dark theme variable overrides
        └── _index.scss
```

### 1.3 — Configure Library `package.json`

`projects/design-system/package.json`:

```json
{
  "name": "@your-org/design-system",
  "version": "1.0.0",
  "description": "Global CSS design system — tokens, typography, components, themes",
  "license": "MIT",
  "sideEffects": ["*.css", "*.scss"],
  "peerDependencies": {
    "@angular/core": "^19.0.0"
  },
  "dependencies": {}
}
```

> ⚠️ `"sideEffects": ["*.css", "*.scss"]` is critical. Without it, bundlers may tree-shake away your global styles thinking they are unused.

-----

## Phase 2 — Author the SCSS

### 2.1 — Design Tokens (`tokens/_colors.scss`)

Define everything as CSS custom properties so consumers can override at runtime:

```scss
// tokens/_colors.scss

:root {
  // Brand
  --color-primary-50:  #eff6ff;
  --color-primary-100: #dbeafe;
  --color-primary-500: #3b82f6;
  --color-primary-600: #2563eb;
  --color-primary-700: #1d4ed8;
  --color-primary-900: #1e3a8a;

  // Neutrals
  --color-gray-50:  #f9fafb;
  --color-gray-100: #f3f4f6;
  --color-gray-500: #6b7280;
  --color-gray-900: #111827;

  // Semantic
  --color-success: #16a34a;
  --color-warning: #d97706;
  --color-error:   #dc2626;
  --color-info:    #0284c7;

  // Surface
  --color-background: var(--color-gray-50);
  --color-surface:    #ffffff;
  --color-border:     var(--color-gray-100);
}
```

### 2.2 — Spacing Tokens (`tokens/_spacing.scss`)

```scss
// tokens/_spacing.scss

:root {
  --space-1:  0.25rem;   //  4px
  --space-2:  0.5rem;    //  8px
  --space-3:  0.75rem;   // 12px
  --space-4:  1rem;      // 16px
  --space-6:  1.5rem;    // 24px
  --space-8:  2rem;      // 32px
  --space-12: 3rem;      // 48px
  --space-16: 4rem;      // 64px

  // Semantic spacing aliases
  --space-component-gap:  var(--space-4);
  --space-section-gap:    var(--space-8);
  --space-page-padding:   var(--space-6);
}
```

### 2.3 — Tokens Barrel (`tokens/_index.scss`)

```scss
// tokens/_index.scss
@forward 'colors';
@forward 'spacing';
@forward 'elevation';
@forward 'breakpoints';
```

> ✅ Use `@forward` (not `@import`) throughout the library — it’s the modern Sass module system and avoids variable leaking.

### 2.4 — Typography (`typography/_scale.scss`)

```scss
// typography/_scale.scss

:root {
  --font-family-base: 'Inter', system-ui, -apple-system, sans-serif;
  --font-family-mono: 'JetBrains Mono', 'Courier New', monospace;

  // Scale
  --font-size-xs:   0.75rem;    // 12px
  --font-size-sm:   0.875rem;   // 14px
  --font-size-base: 1rem;       // 16px
  --font-size-lg:   1.125rem;   // 18px
  --font-size-xl:   1.25rem;    // 20px
  --font-size-2xl:  1.5rem;     // 24px
  --font-size-3xl:  1.875rem;   // 30px
  --font-size-4xl:  2.25rem;    // 36px

  // Line heights
  --line-height-tight:  1.25;
  --line-height-normal: 1.5;
  --line-height-relaxed: 1.75;

  // Weights
  --font-weight-regular: 400;
  --font-weight-medium:  500;
  --font-weight-semibold: 600;
  --font-weight-bold:    700;
}

// Base typography resets applied globally
body {
  font-family: var(--font-family-base);
  font-size:   var(--font-size-base);
  line-height: var(--line-height-normal);
  color:       var(--color-gray-900);
}

h1 { font-size: var(--font-size-4xl); font-weight: var(--font-weight-bold);    line-height: var(--line-height-tight); }
h2 { font-size: var(--font-size-3xl); font-weight: var(--font-weight-semibold); line-height: var(--line-height-tight); }
h3 { font-size: var(--font-size-2xl); font-weight: var(--font-weight-semibold); }
h4 { font-size: var(--font-size-xl);  font-weight: var(--font-weight-medium); }
h5 { font-size: var(--font-size-lg);  font-weight: var(--font-weight-medium); }
h6 { font-size: var(--font-size-base); font-weight: var(--font-weight-medium); }
```

### 2.5 — Component Styles (`components/_button.scss`)

```scss
// components/_button.scss
// Uses tokens via CSS variables — no SCSS variable dependencies

.btn {
  display:         inline-flex;
  align-items:     center;
  justify-content: center;
  gap:             var(--space-2);
  padding:         var(--space-2) var(--space-4);
  font-size:       var(--font-size-sm);
  font-weight:     var(--font-weight-medium);
  border-radius:   0.375rem;
  border:          1px solid transparent;
  cursor:          pointer;
  transition:      background-color 150ms ease, border-color 150ms ease;

  // Variants
  &--primary {
    background-color: var(--color-primary-600);
    color:            #fff;

    &:hover  { background-color: var(--color-primary-700); }
    &:active { background-color: var(--color-primary-900); }
  }

  &--secondary {
    background-color: transparent;
    border-color:     var(--color-primary-600);
    color:            var(--color-primary-600);

    &:hover { background-color: var(--color-primary-50); }
  }

  &--ghost {
    background-color: transparent;
    color:            var(--color-gray-500);

    &:hover { background-color: var(--color-gray-100); }
  }

  // Sizes
  &--sm { padding: var(--space-1) var(--space-2); font-size: var(--font-size-xs); }
  &--lg { padding: var(--space-3) var(--space-6); font-size: var(--font-size-lg); }

  // States
  &:disabled {
    opacity: 0.5;
    cursor:  not-allowed;
  }
}
```

### 2.6 — Themes (`themes/_dark.scss`)

```scss
// themes/_dark.scss
// Override CSS variables under a [data-theme="dark"] attribute

[data-theme="dark"] {
  --color-background: #0f172a;
  --color-surface:    #1e293b;
  --color-border:     #334155;
  --color-gray-900:   #f8fafc;   // Flip text to light
  --color-gray-500:   #94a3b8;

  --color-primary-500: #60a5fa;
  --color-primary-600: #3b82f6;
}
```

### 2.7 — Master Entry Point (`src/index.scss`)

```scss
// src/index.scss — imports everything in dependency order

// 1. Tokens first (everything else depends on these)
@use 'tokens/index' as *;

// 2. Typography (depends on color + spacing tokens)
@use 'typography/index' as *;

// 3. Component styles (depend on tokens)
@use 'components/index' as *;

// 4. Themes last (override token values)
@use 'themes/index' as *;
```

-----

## Phase 3 — Configure ng-packagr for CSS Output

### 3.1 — `ng-package.json`

```json
{
  "$schema": "../../node_modules/ng-packagr/ng-package.schema.json",
  "lib": {
    "entryFile": "src/public-api.ts",
    "styleIncludePaths": ["src"]
  },
  "assets": [
    {
      "glob": "**/*.scss",
      "input": "src",
      "output": "."
    }
  ]
}
```

> ✅ The `assets` block copies raw `.scss` source files into `dist/` so consumers can `@use` individual partials (e.g. tokens only) without importing the full compiled CSS.

### 3.2 — `public-api.ts`

For a CSS-only library this is minimal — its main purpose is satisfying ng-packagr’s entry file requirement:

```typescript
// src/public-api.ts
// This library is CSS-only. SCSS partials are consumed directly.
// Exporting a version constant enables consumers to verify the installed version.
export const DESIGN_SYSTEM_VERSION = '1.0.0';
```

### 3.3 — `tsconfig.lib.json`

```json
{
  "extends": "../../tsconfig.json",
  "compilerOptions": {
    "outDir": "../../out-tsc/lib",
    "declaration": true,
    "declarationMap": true,
    "inlineSources": true,
    "types": []
  },
  "exclude": ["**/*.spec.ts"]
}
```

### 3.4 — Root `angular.json` — Add `stylePreprocessorOptions`

In the `build` target for the library, add SCSS include paths so partials resolve correctly:

```json
{
  "projects": {
    "design-system": {
      "architect": {
        "build": {
          "options": {
            "project": "projects/design-system/ng-package.json",
            "stylePreprocessorOptions": {
              "includePaths": [
                "projects/design-system/src"
              ]
            }
          }
        }
      }
    }
  }
}
```

-----

## Phase 4 — Build & Verify

### 4.1 — Build the Library

```bash
ng build design-system --configuration production
```

### 4.2 — Expected `dist/` Output

```
dist/design-system/
├── package.json              ← Auto-generated by ng-packagr
├── index.d.ts                ← Type declaration for the version export
├── esm2022/
│   └── design-system.mjs     ← JS wrapper (minimal for CSS-only lib)
├── fesm2022/
│   └── design-system.mjs
│
├── _index.scss               ← ✅ Master SCSS entry (for @use in consumers)
├── tokens/
│   ├── _colors.scss
│   ├── _spacing.scss
│   ├── _elevation.scss
│   ├── _breakpoints.scss
│   └── _index.scss
├── typography/
│   └── _index.scss  (+ partials)
├── components/
│   └── _index.scss  (+ partials)
└── themes/
    └── _index.scss  (+ partials)
```

### 4.3 — Verify SCSS Assets Are Present

```bash
# All SCSS partials should be in dist/
find dist/design-system -name "*.scss" | sort

# Verify tokens partial is importable
cat dist/design-system/tokens/_colors.scss
```

### 4.4 — Local Smoke Test Before Publishing

Link the built library into a local consumer app to verify styles apply:

```bash
# In Repo A
cd dist/design-system
npm link

# In Repo B (local)
npm link @your-org/design-system
```

Then add to `styles.scss` in the consumer and run `ng serve` to verify.

-----

## Phase 5 — Package & Publish via Jenkins → S3

### 5.1 — S3 Bucket Structure

```
s3://your-artifact-bucket/
└── design-system/
    ├── 1.0.0/
    │   └── your-org-design-system-1.0.0.tgz
    ├── 1.1.0/
    │   └── your-org-design-system-1.1.0.tgz
    └── latest/
        └── your-org-design-system-latest.tgz  ← dev/testing only
```

> Versioned paths are **immutable**. Never overwrite a published version.

### 5.2 — Jenkinsfile

```groovy
pipeline {
  agent any

  environment {
    S3_BUCKET    = 'your-artifact-bucket'
    S3_PREFIX    = 'design-system'
    CDN_BASE     = 'https://cdn.your-org.com'
    NODE_VERSION = '20'
  }

  stages {

    stage('Setup') {
      steps {
        sh "nvm use ${NODE_VERSION} || nvm install ${NODE_VERSION}"
        sh 'npm ci'
      }
    }

    stage('Lint SCSS') {
      steps {
        // Optional: add stylelint for SCSS quality gate
        sh 'npx stylelint "projects/design-system/src/**/*.scss"'
      }
    }

    stage('Build') {
      steps {
        sh 'ng build design-system --configuration production'
      }
    }

    stage('Verify Assets') {
      steps {
        sh '''
          echo "Checking SCSS assets in dist..."
          find dist/design-system -name "*.scss" | sort
          test -f dist/design-system/tokens/_colors.scss || (echo "❌ tokens missing" && exit 1)
          test -f dist/design-system/_index.scss         || (echo "❌ master index missing" && exit 1)
          echo "✅ All SCSS assets present"
        '''
      }
    }

    stage('Pack') {
      steps {
        script {
          def libPkg    = readJSON file: 'projects/design-system/package.json'
          env.LIB_VERSION = libPkg.version
          env.TGZ_NAME    = "your-org-design-system-${env.LIB_VERSION}.tgz"
        }
        sh 'npm pack dist/design-system'
        sh "ls -lh ${env.TGZ_NAME}"
      }
    }

    stage('Upload to S3') {
      steps {
        sh """
          # Versioned upload — immutable, long cache TTL
          aws s3 cp ${env.TGZ_NAME} \
            s3://${S3_BUCKET}/${S3_PREFIX}/${env.LIB_VERSION}/${env.TGZ_NAME} \
            --cache-control "public, max-age=31536000, immutable"

          # Latest pointer — short TTL, for dev pipelines only
          aws s3 cp ${env.TGZ_NAME} \
            s3://${S3_BUCKET}/${S3_PREFIX}/latest/your-org-design-system-latest.tgz \
            --cache-control "public, max-age=300"
        """
      }
    }

    stage('Notify') {
      steps {
        script {
          def url = "${CDN_BASE}/${S3_PREFIX}/${env.LIB_VERSION}/${env.TGZ_NAME}"
          echo "✅ Published design-system v${env.LIB_VERSION}"
          echo "📦 CDN URL: ${url}"
        }
      }
    }
  }

  post {
    failure {
      echo '❌ Pipeline failed — no artifact was published.'
    }
    cleanup {
      sh 'rm -f *.tgz'
    }
  }
}
```

### 5.3 — IAM Policy for Jenkins Agent

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:GetObject", "s3:ListBucket"],
      "Resource": [
        "arn:aws:s3:::your-artifact-bucket",
        "arn:aws:s3:::your-artifact-bucket/design-system/*"
      ]
    }
  ]
}
```

-----

## Phase 6 — Serve via CloudFront

### 6.1 — CloudFront Configuration

|Setting                        |Value                                                |
|-------------------------------|-----------------------------------------------------|
|Origin                         |`your-artifact-bucket.s3.amazonaws.com`              |
|Origin access                  |OAC (Origin Access Control) — S3 bucket stays private|
|Viewer protocol                |HTTPS only                                           |
|Cache — versioned paths (`/*/`)|`max-age=31536000, immutable`                        |
|Cache — latest path            |`max-age=300`                                        |

### 6.2 — Resulting CDN URLs

```
# Versioned — use in production consumer package.json
https://cdn.your-org.com/design-system/1.0.0/your-org-design-system-1.0.0.tgz

# Latest — use only in dev/preview pipelines
https://cdn.your-org.com/design-system/latest/your-org-design-system-latest.tgz
```

-----

## Phase 7 — Consume in Repo B (Global Level)

Global consumption means the design system’s compiled CSS — tokens, typography resets, component base styles — loads once for the entire app.

### 7.1 — Install the Package

```bash
npm install https://cdn.your-org.com/design-system/1.0.0/your-org-design-system-1.0.0.tgz
```

`package.json` in Repo B:

```json
{
  "dependencies": {
    "@your-org/design-system": "https://cdn.your-org.com/design-system/1.0.0/your-org-design-system-1.0.0.tgz"
  }
}
```

### 7.2 — Register SCSS Include Path

In `angular.json` of Repo B, add the node_modules path so SCSS partials resolve:

```json
{
  "projects": {
    "your-app": {
      "architect": {
        "build": {
          "options": {
            "stylePreprocessorOptions": {
              "includePaths": [
                "node_modules/@your-org/design-system"
              ]
            }
          }
        }
      }
    }
  }
}
```

### 7.3 — Import in Global `styles.scss`

```scss
// src/styles.scss

// ✅ Option A: Import everything (tokens + typography + components + themes)
@use '@your-org/design-system' as ds;

// ✅ Option B: Import selectively — only what the app needs globally
@use '@your-org/design-system/tokens/index' as *;
@use '@your-org/design-system/typography/index' as *;
@use '@your-org/design-system/themes/index' as *;
// Skip components — load them at component level instead (see Phase 8)
```

### 7.4 — Register in `angular.json` Styles Array (Alternative)

For apps that prefer not to touch `styles.scss`, register the compiled output directly:

```json
{
  "projects": {
    "your-app": {
      "architect": {
        "build": {
          "options": {
            "styles": [
              "src/styles.scss",
              "node_modules/@your-org/design-system/_index.scss"
            ]
          }
        }
      }
    }
  }
}
```

> ✅ This approach keeps the global import completely separate from the app’s own SCSS, which is cleaner for teams that want strict separation.

### 7.5 — Verify Tokens Are Available

After running `ng serve`, open DevTools and check that CSS variables are on `:root`:

```
--color-primary-600: #2563eb  ✅
--font-size-base: 1rem         ✅
--space-4: 1rem                ✅
```

-----

## Phase 8 — Consume in Repo B (Component Level)

Component-level consumption lets individual Angular components `@use` specific partials (e.g. tokens only) without re-importing the full design system.

### 8.1 — Use Tokens Inside a Component’s SCSS

```scss
// button.component.scss
// Import only the tokens partial — no full design system re-import needed
@use '@your-org/design-system/tokens/colors' as colors;
@use '@your-org/design-system/tokens/spacing' as spacing;

:host {
  display: inline-block;
}

.custom-btn {
  background-color: var(--color-primary-600);   // CSS variable (runtime)
  padding: var(--space-2) var(--space-4);        // CSS variable (runtime)
  border-radius: 0.375rem;
}
```

> ✅ Because tokens are CSS custom properties on `:root`, components can reference them as `var(--token-name)` without any SCSS `@use` at all — as long as the global import (Phase 7) loaded them first.

### 8.2 — Use Component Styles from the Library

If Repo B uses the library’s pre-built `.btn` classes directly in templates:

```html
<!-- app.component.html -->
<button class="btn btn--primary btn--lg">Save</button>
<button class="btn btn--secondary">Cancel</button>
```

These classes are available globally because `components/_index.scss` was imported in `styles.scss` (Phase 7).

### 8.3 — Extend Library Styles in a Component

```scss
// card.component.scss
@use '@your-org/design-system/components/card' as *;

// Extend with app-specific overrides
.card {
  // Inherits base card styles from design system
  border: 1px solid var(--color-border);

  // App-specific extension
  &--dashboard {
    min-height: 200px;
    grid-column: span 2;
  }
}
```

### 8.4 — ViewEncapsulation Consideration

Angular’s default `ViewEncapsulation.Emulated` scopes component styles. For design system classes applied from the global stylesheet to work inside component templates, keep the default — **do not** use `ViewEncapsulation.None` unless intentional:

```typescript
@Component({
  selector: 'app-card',
  templateUrl: './card.component.html',
  styleUrls: ['./card.component.scss'],
  // encapsulation: ViewEncapsulation.None  ← avoid unless you need it
})
export class CardComponent {}
```

-----

## Phase 9 — Theming (Dark / Light Mode)

### 9.1 — How Themes Work

Themes override CSS custom properties under a `[data-theme]` attribute. No JavaScript class toggling, no separate stylesheet loading — just a single attribute on `<html>` or `<body>`.

```html
<!-- Light (default, no attribute needed) -->
<html>

<!-- Dark -->
<html data-theme="dark">
```

### 9.2 — Theme Toggle Service in Repo B

```typescript
// theme.service.ts
import { Injectable, Renderer2, RendererFactory2 } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class ThemeService {
  private renderer: Renderer2;
  private currentTheme: 'light' | 'dark' = 'light';

  constructor(rendererFactory: RendererFactory2) {
    this.renderer = rendererFactory.createRenderer(null, null);
  }

  setTheme(theme: 'light' | 'dark'): void {
    this.currentTheme = theme;
    const html = document.documentElement;

    if (theme === 'dark') {
      this.renderer.setAttribute(html, 'data-theme', 'dark');
    } else {
      this.renderer.removeAttribute(html, 'data-theme');
    }

    localStorage.setItem('theme', theme);
  }

  toggleTheme(): void {
    this.setTheme(this.currentTheme === 'light' ? 'dark' : 'light');
  }

  initTheme(): void {
    const saved = localStorage.getItem('theme') as 'light' | 'dark' | null;
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    this.setTheme(saved ?? (prefersDark ? 'dark' : 'light'));
  }
}
```

### 9.3 — Initialise Theme on App Load

```typescript
// app.component.ts
import { Component, OnInit, inject } from '@angular/core';
import { ThemeService } from './theme.service';

@Component({
  selector: 'app-root',
  template: `<router-outlet />`
})
export class AppComponent implements OnInit {
  private theme = inject(ThemeService);

  ngOnInit(): void {
    this.theme.initTheme();   // Reads saved preference or system preference
  }
}
```

### 9.4 — Respect System Preference Automatically (CSS Only)

Add this to `themes/_dark.scss` for zero-JS dark mode based on OS setting:

```scss
// themes/_dark.scss

// Explicit data attribute (controlled by ThemeService)
[data-theme="dark"] {
  --color-background: #0f172a;
  --color-surface:    #1e293b;
  // ... other overrides
}

// Automatic — follows OS preference when no data-theme is set
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --color-background: #0f172a;
    --color-surface:    #1e293b;
    // ... same overrides
  }
}
```

-----

## Phase 10 — Updating the Library

### 10.1 — Release a New Version

```bash
# 1. Make SCSS changes in projects/design-system/src/

# 2. Bump version in projects/design-system/package.json
#    e.g. "version": "1.1.0"

# 3. Commit and tag
git add projects/design-system/
git commit -m "feat: add badge component styles"
git tag -a v1.1.0 -m "Release v1.1.0"
git push origin main --follow-tags
# Jenkins pipeline triggers automatically ↑
```

### 10.2 — Update in Consumer Repo B

```bash
npm install https://cdn.your-org.com/design-system/1.1.0/your-org-design-system-1.1.0.tgz
git add package.json package-lock.json
git commit -m "chore: update design-system to v1.1.0"
```

### 10.3 — Breaking Change Protocol

When changing token names or removing component classes (a breaking change), bump the **major** version and document the migration:

```scss
// ❌ Old (v1): --color-primary
// ✅ New (v2): --color-primary-600

// Provide a compatibility shim in themes/_compat.scss for one release cycle:
:root {
  --color-primary: var(--color-primary-600);  // deprecated alias
}
```

-----

## Best Practices

### SCSS Architecture

- Use `@use` and `@forward` — never `@import` (deprecated in Dart Sass)
- All values in component styles must reference CSS variables, not hardcoded values
- Keep SCSS partials small and single-purpose — one file per concept
- Barrel files (`_index.scss`) in each folder keep imports clean

### Token Design

- Prefix all CSS variables with `--color-`, `--space-`, `--font-` for discoverability
- Use semantic aliases (`--color-background`) that point to palette tokens (`--color-gray-50`) — consumers override semantics, not palette
- Document every token with a comment explaining intent, not just value

### Versioning

- Never overwrite a published S3 artifact — always bump the version
- Use annotated Git tags for every release
- Maintain a `CHANGELOG.md` so consumer teams know what changed

### Consumer Integration

- Load the design system **once globally** via `styles.scss` or `angular.json styles[]`
- Use CSS variables at runtime (`var(--token)`) — avoid SCSS variable dependencies across the boundary
- Test both light and dark themes in consumer CI

-----

## Common Mistakes

|Mistake                                               |Problem                                                     |Fix                                                          |
|------------------------------------------------------|------------------------------------------------------------|-------------------------------------------------------------|
|Using `@import` instead of `@use`/`@forward`          |Deprecated, causes variable leaks, will break in future Sass|Replace all `@import` with `@use`/`@forward`                 |
|Omitting `"sideEffects": ["*.css","*.scss"]`          |Bundler tree-shakes global styles — app loads with no styles|Always declare sideEffects in library `package.json`         |
|Hardcoding values in component styles                 |Styles don’t respond to theme changes                       |Always use `var(--token-name)`                               |
|Not copying SCSS assets in `ng-package.json`          |Consumers can’t `@use` partials — only get compiled JS      |Add `assets` block to `ng-package.json`                      |
|Importing full design system in every component       |CSS duplicated across component bundles                     |Import full system globally once; use `var()` in components  |
|Using `ViewEncapsulation.None` by default             |Component styles bleed into the global scope                |Keep default `Emulated`; use global styles for global classes|
|Publishing to `latest` S3 path in production consumers|Non-deterministic installs                                  |Pin to versioned CDN URL in `package.json`                   |
|Changing token names in a minor/patch release         |Breaks consumers silently                                   |Token renames are always major version bumps                 |

-----

## Limitations & Mitigations

|Limitation                                          |Severity|Mitigation                                                                           |
|----------------------------------------------------|--------|-------------------------------------------------------------------------------------|
|No `npm outdated` support for CDN-hosted packages   |Medium  |Maintain a version changelog and notify consumer teams on release                    |
|No `npm audit` on `.tgz` from CDN                   |Medium  |Run Snyk or OWASP scans in the Jenkins pipeline as a gate                            |
|SCSS `@use` paths must match dist structure exactly |Medium  |Verify `find dist/design-system -name "*.scss"` in CI before publish                 |
|Theme flash on page load (FOUC)                     |Low     |Inline a tiny theme-init script in `index.html` `<head>` before Angular loads        |
|CloudFront caches old artifact if version not bumped|High    |S3 versioned paths are immutable — enforce version bump in Jenkins as a required step|

-----

## Quick Reference Cheatsheet

### Repo A — Release

```bash
# 1. Bump version in projects/design-system/package.json
# 2. Commit + tag
git add projects/design-system/package.json
git commit -m "chore: bump design-system to v1.x.x"
git tag -a v1.x.x -m "Release v1.x.x"
git push origin main --follow-tags
# Jenkins builds, packs, uploads automatically
```

### Jenkins — Core Steps

```bash
npm ci
npx stylelint "projects/design-system/src/**/*.scss"
ng build design-system --configuration production
npm pack dist/design-system
aws s3 cp your-org-design-system-1.x.x.tgz \
  s3://your-bucket/design-system/1.x.x/your-org-design-system-1.x.x.tgz \
  --cache-control "public, max-age=31536000, immutable"
```

### Repo B — Install / Update

```bash
# Install
npm install https://cdn.your-org.com/design-system/1.0.0/your-org-design-system-1.0.0.tgz

# Update
npm install https://cdn.your-org.com/design-system/1.1.0/your-org-design-system-1.1.0.tgz

# Clean install in CI
npm ci
```

### Consumer `styles.scss` Import Patterns

```scss
// Full import (everything)
@use '@your-org/design-system' as ds;

// Selective imports
@use '@your-org/design-system/tokens/index' as *;
@use '@your-org/design-system/typography/index' as *;
@use '@your-org/design-system/themes/index' as *;

// In a component — tokens only
@use '@your-org/design-system/tokens/colors' as colors;
```

### Theme Toggle

```typescript
// Set dark
themeService.setTheme('dark');   // → <html data-theme="dark">

// Set light
themeService.setTheme('light');  // → <html>

// Toggle
themeService.toggleTheme();
```

-----

*Last updated: v3.0 — Rewritten to focus on global CSS / SCSS design system: design tokens, typography, component styles, dark/light theming, ng-packagr SCSS asset pipeline, Jenkins + S3 + CloudFront distribution.*