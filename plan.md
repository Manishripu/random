# 🚀 Portal Release Sanity Automation Tool - Complete Implementation Plan

**Version:** 1.0  
**Last Updated:** January 2026  
**Status:** Production-Ready Specification  
**Document Type:** Super Prompt - Complete Implementation Guide

-----

## Table of Contents

1. [Executive Summary](#1-executive-summary)
1. [System Architecture](#2-system-architecture)
1. [Technology Stack & Dependencies](#3-technology-stack--dependencies)
1. [Project Structure](#4-project-structure)
1. [Browser Attachment & Session Management](#5-browser-attachment--session-management)
1. [Workflow Framework](#6-workflow-framework)
1. [Validation & Assertion Layer](#7-validation--assertion-layer)
1. [Error Handling & Recovery](#8-error-handling--recovery)
1. [Reporting & Evidence Collection](#9-reporting--evidence-collection)
1. [Configuration Management](#10-configuration-management)
1. [Workflow Implementations](#11-workflow-implementations)
1. [Test Data Management](#12-test-data-management)
1. [CI/CD Integration](#13-cicd-integration)
1. [Development Guidelines](#14-development-guidelines)
1. [Complete Code Reference](#15-complete-code-reference)
1. [Troubleshooting Guide](#16-troubleshooting-guide)

-----

## 1. Executive Summary

### 1.1 Purpose

This tool automates post-release sanity validation by executing critical business workflows against a live portal environment. It operates on an already-authenticated Chrome session, mimicking real user behavior to detect regressions, rendering issues, and functional defects.

### 1.2 Core Principles

- **Zero Authentication Logic**: Attaches to pre-authenticated browser
- **Human-First Validation**: Tests what users actually do
- **Deterministic Execution**: Same inputs always produce same results
- **Evidence-Based Failure**: Every failure includes screenshots, traces, and logs
- **Fail-Fast Philosophy**: Any critical error immediately fails the entire run
- **Self-Cleaning**: Automatically removes test data after execution

### 1.3 Success Criteria

✅ Connects to running Chrome within 5 seconds  
✅ Executes all workflows in under 10 minutes  
✅ Produces actionable PASS/FAIL report with evidence  
✅ Zero false positives (no flaky tests)  
✅ Catches 95%+ of critical regressions  
✅ Runs successfully on any environment (dev/staging/prod)

### 1.4 Key Features

- **Chrome Attachment**: Connects to existing browser via CDP
- **Session Validation**: Verifies authentication before tests
- **Workflow Orchestration**: Sequential or parallel execution
- **Multi-Layer Validation**: Console, Network, Rendering, A11y
- **Rich Reporting**: JSON, HTML, Slack notifications
- **Automatic Cleanup**: Removes all test data
- **Trace Recording**: Full Playwright traces for debugging

-----

## 2. System Architecture

### 2.1 High-Level Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 1: SETUP                                                 │
│  ├─ Engineer starts Chrome with --remote-debugging-port=9222   │
│  ├─ Engineer logs into portal manually                         │
│  └─ Engineer confirms authentication is complete               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 2: ATTACHMENT                                            │
│  ├─ Tool connects via CDP (Chrome DevTools Protocol)           │
│  ├─ Detects active tab with portal URL                         │
│  ├─ Validates session is authenticated                         │
│  └─ Captures initial state (cookies, localStorage, session)    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 3: WORKFLOW EXECUTION                                    │
│  ├─ For each workflow:                                         │
│  │   ├─ Navigate to start route                               │
│  │   ├─ Execute workflow steps                                │
│  │   ├─ Validate success criteria                             │
│  │   ├─ Check for console errors                              │
│  │   ├─ Verify rendering integrity                            │
│  │   ├─ Capture evidence (screenshots, traces)                │
│  │   └─ Clean up test data                                    │
│  └─ Continue until all workflows complete or critical failure  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 4: REPORTING                                             │
│  ├─ Aggregate results from all workflows                       │
│  ├─ Generate summary.json with detailed metrics                │
│  ├─ Create HTML report with embedded screenshots               │
│  ├─ Send Slack/Email notification (optional)                   │
│  └─ Exit with code 0 (PASS) or 1 (FAIL)                       │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Component Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    CLI Entry Point                           │
│                    (runner/attach.ts)                        │
└──────────────────┬───────────────────────────────────────────┘
                   │
                   ├─────→ Browser Manager ───→ CDP Connection
                   │        (session.ts)         (Playwright)
                   │
                   ├─────→ Workflow Orchestrator
                   │        ├─ Workflow Loader
                   │        ├─ Execution Engine
                   │        └─ Parallel/Sequential Runner
                   │
                   ├─────→ Validation Layer
                   │        ├─ Console Monitor
                   │        ├─ Network Monitor
                   │        ├─ Rendering Validator
                   │        └─ Assertion Engine
                   │
                   ├─────→ Evidence Collector
                   │        ├─ Screenshot Capture
                   │        ├─ Trace Recording
                   │        ├─ Log Aggregation
                   │        └─ HAR Export
                   │
                   └─────→ Reporter
                            ├─ JSON Generator
                            ├─ HTML Generator
                            └─ Notification Dispatcher
```

### 2.3 Data Flow Diagram

```
User Action          System Component           Output
─────────────────────────────────────────────────────────
Start Chrome    →    Chrome Process        →    CDP Endpoint
                                                 (localhost:9222)
                          ↓
Manual Login    →    Browser Session       →    Auth Cookies
                                                 Session Tokens
                          ↓
Run Tool        →    SessionManager        →    Connected Page
                          ↓
Execute Tests   →    WorkflowOrchestrator  →    Workflow Results
                          ↓
Validate        →    CheckEngine           →    Error Detection
                          ↓
Capture         →    EvidenceCollector     →    Screenshots
                                                 Traces
                                                 Logs
                          ↓
Report          →    Reporter              →    HTML/JSON
                                                 Notifications
```

-----

## 3. Technology Stack & Dependencies

### 3.1 Core Dependencies

```json
{
  "name": "portal-sanity",
  "version": "1.0.0",
  "description": "Portal release sanity automation tool",
  "main": "dist/runner/attach.js",
  "scripts": {
    "build": "tsc",
    "sanity": "tsx src/runner/attach.ts",
    "sanity:debug": "tsx src/runner/attach.ts --debug",
    "sanity:parallel": "tsx src/runner/attach.ts --parallel",
    "clean": "rm -rf dist output",
    "lint": "eslint src/**/*.ts",
    "format": "prettier --write src/**/*.ts"
  },
  "dependencies": {
    "@playwright/test": "^1.40.0",
    "playwright": "^1.40.0",
    "typescript": "^5.3.0",
    "zod": "^3.22.0",
    "chalk": "^5.3.0",
    "ora": "^8.0.0",
    "date-fns": "^3.0.0",
    "commander": "^11.1.0"
  },
  "devDependencies": {
    "@types/node": "^20.10.0",
    "tsx": "^4.7.0",
    "prettier": "^3.1.0",
    "eslint": "^8.56.0",
    "@typescript-eslint/eslint-plugin": "^6.15.0",
    "@typescript-eslint/parser": "^6.15.0"
  },
  "optionalDependencies": {
    "@slack/web-api": "^6.11.0",
    "nodemailer": "^6.9.0",
    "sharp": "^0.33.0"
  },
  "engines": {
    "node": ">=18.0.0"
  }
}
```

### 3.2 TypeScript Configuration

**File: `tsconfig.json`**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "commonjs",
    "lib": ["ES2022"],
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,
    "moduleResolution": "node",
    "allowSyntheticDefaultImports": true,
    "types": ["node", "@playwright/test"]
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist", "output"]
}
```

### 3.3 Playwright Configuration

**File: `playwright.config.ts`**

```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './src/workflows',
  timeout: 60000,
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: 0,
  workers: 1,
  
  reporter: [
    ['list'],
    ['html', { open: 'never', outputFolder: 'output/playwright-report' }],
  ],

  use: {
    actionTimeout: 10000,
    navigationTimeout: 30000,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
```

### 3.4 System Requirements

|Component           |Requirement                    |
|--------------------|-------------------------------|
|**Node.js**         |>= 18.0.0                      |
|**Chrome**          |>= 120 (with CDP enabled)      |
|**Operating System**|Linux, macOS, Windows 10+      |
|**Memory**          |>= 4GB available RAM           |
|**Disk Space**      |>= 500MB for traces/screenshots|
|**Network**         |Stable connection to portal    |

-----

## 4. Project Structure

```
portal-sanity/
│
├── src/
│   ├── runner/
│   │   ├── attach.ts                    # Main entry point
│   │   ├── orchestrator.ts              # Workflow execution manager
│   │   └── session.ts                   # Browser session manager
│   │
│   ├── workflows/
│   │   ├── base.workflow.ts             # Abstract base class
│   │   ├── dashboard.workflow.ts        # Dashboard load test
│   │   ├── content.create.workflow.ts   # Content creation
│   │   ├── content.edit.workflow.ts     # Content editing
│   │   ├── content.publish.workflow.ts  # Content publishing
│   │   ├── content.delete.workflow.ts   # Content deletion
│   │   ├── search.workflow.ts           # Search functionality
│   │   ├── permissions.workflow.ts      # Permission checks
│   │   ├── media.upload.workflow.ts     # Media upload
│   │   └── user.profile.workflow.ts     # User profile updates
│   │
│   ├── checks/
│   │   ├── console.check.ts             # Console error detection
│   │   ├── network.check.ts             # API failure detection
│   │   ├── rendering.check.ts           # Layout shift, visibility
│   │   ├── accessibility.check.ts       # A11y violations
│   │   └── performance.check.ts         # Load time, LCP, FID
│   │
│   ├── validators/
│   │   ├── element.validator.ts         # DOM element assertions
│   │   ├── api.validator.ts             # Response validation
│   │   ├── state.validator.ts           # Application state checks
│   │   └── custom.matchers.ts           # Playwright custom matchers
│   │
│   ├── evidence/
│   │   ├── screenshot.ts                # Screenshot capture
│   │   ├── trace.ts                     # Trace recording
│   │   ├── har.ts                       # Network HAR export
│   │   └── collector.ts                 # Evidence aggregator
│   │
│   ├── cleanup/
│   │   ├── strategies/
│   │   │   ├── content.cleanup.ts       # Content cleanup
│   │   │   ├── media.cleanup.ts         # Media cleanup
│   │   │   └── user.cleanup.ts          # User data cleanup
│   │   └── cleanup.manager.ts           # Cleanup orchestrator
│   │
│   ├── report/
│   │   ├── generators/
│   │   │   ├── json.generator.ts        # JSON report
│   │   │   ├── html.generator.ts        # HTML report
│   │   │   └── markdown.generator.ts    # Markdown summary
│   │   ├── notifiers/
│   │   │   ├── slack.notifier.ts        # Slack notifications
│   │   │   └── email.notifier.ts        # Email notifications
│   │   └── reporter.ts                  # Report orchestrator
│   │
│   ├── config/
│   │   ├── sanity.config.ts             # Master configuration
│   │   ├── routes.ts                    # Portal routes
│   │   ├── selectors.ts                 # CSS/XPath selectors
│   │   ├── timeouts.ts                  # Timeout configurations
│   │   └── environments.ts              # Environment-specific settings
│   │
│   ├── utils/
│   │   ├── wait.ts                      # Smart wait utilities
│   │   ├── retry.ts                     # Retry logic
│   │   ├── logger.ts                    # Structured logging
│   │   └── crypto.ts                    # ID generation
│   │
│   └── types/
│       ├── workflow.types.ts            # Workflow type definitions
│       ├── report.types.ts              # Report type definitions
│       ├── config.types.ts              # Config type definitions
│       └── evidence.types.ts            # Evidence type definitions
│
├── output/
│   ├── reports/
│   │   └── {timestamp}/
│   │       ├── summary.json
│   │       ├── report.html
│   │       └── evidence/
│   ├── traces/
│   └── screenshots/
│
├── scripts/
│   ├── start-chrome.sh                  # Launch Chrome with CDP
│   ├── start-chrome.bat                 # Windows version
│   ├── run-sanity.sh                    # Execute sanity suite
│   └── cleanup-output.sh                # Clean old reports
│
├── .github/
│   └── workflows/
│       └── sanity.yml                   # CI/CD workflow
│
├── .env.example
├── .gitignore
├── .eslintrc.json
├── .prettierrc
├── playwright.config.ts
├── tsconfig.json
├── package.json
└── README.md
```

-----

## 5. Browser Attachment & Session Management

### 5.1 Chrome Launch Script

**File: `scripts/start-chrome.sh`**

```bash
#!/bin/bash

# Start Chrome with remote debugging enabled
# Usage: ./scripts/start-chrome.sh [port]

set -e

PORT=${1:-9222}
PROFILE_DIR="/tmp/chrome-sanity-profile"

echo "🚀 Portal Sanity - Chrome Launcher"
echo "=================================="

# Kill existing Chrome instances on this port
echo "🔍 Checking for existing Chrome instances on port $PORT..."
if lsof -ti:$PORT >/dev/null 2>&1; then
    echo "⚠️  Port $PORT is in use. Killing existing processes..."
    lsof -ti:$PORT | xargs kill -9 2>/dev/null || true
    sleep 2
fi

# Create fresh profile directory
echo "📁 Creating fresh profile directory..."
rm -rf "$PROFILE_DIR"
mkdir -p "$PROFILE_DIR"

# Detect OS and launch Chrome
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    if [ ! -f "$CHROME_PATH" ]; then
        echo "❌ Chrome not found at: $CHROME_PATH"
        exit 1
    fi
    
    echo "🍎 Launching Chrome on macOS..."
    "$CHROME_PATH" \
        --remote-debugging-port=$PORT \
        --user-data-dir="$PROFILE_DIR" \
        --no-first-run \
        --no-default-browser-check \
        --disable-features=TranslateUI \
        --disable-popup-blocking \
        "about:blank" &

elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    if command -v google-chrome &> /dev/null; then
        CHROME_CMD="google-chrome"
    elif command -v chromium-browser &> /dev/null; then
        CHROME_CMD="chromium-browser"
    else
        echo "❌ Chrome/Chromium not found"
        exit 1
    fi
    
    echo "🐧 Launching Chrome on Linux..."
    $CHROME_CMD \
        --remote-debugging-port=$PORT \
        --user-data-dir="$PROFILE_DIR" \
        --no-first-run \
        --no-default-browser-check \
        "about:blank" &

else
    # Windows (Git Bash/WSL)
    CHROME_PATH="C:\Program Files\Google\Chrome\Application\chrome.exe"
    if [ ! -f "$CHROME_PATH" ]; then
        echo "❌ Chrome not found at: $CHROME_PATH"
        exit 1
    fi
    
    echo "🪟 Launching Chrome on Windows..."
    "$CHROME_PATH" \
        --remote-debugging-port=$PORT \
        --user-data-dir="$PROFILE_DIR" \
        --no-first-run \
        "about:blank" &
fi

# Wait for Chrome to start
echo "⏳ Waiting for Chrome to start..."
sleep 3

# Verify Chrome is running
if curl -s "http://localhost:$PORT/json/version" > /dev/null; then
    echo "✅ Chrome started successfully!"
    echo ""
    echo "📡 CDP Endpoint: http://localhost:$PORT"
    echo "📁 Profile: $PROFILE_DIR"
    echo ""
    echo "👉 Next steps:"
    echo "   1. Log into the portal manually"
    echo "   2. Run: npm run sanity"
    echo ""
else
    echo "❌ Failed to start Chrome"
    exit 1
fi
```

**File: `scripts/start-chrome.bat`** (Windows)

```batch
@echo off
SET PORT=%1
IF "%PORT%"=="" SET PORT=9222

SET PROFILE_DIR=%TEMP%\chrome-sanity-profile

echo 🚀 Portal Sanity - Chrome Launcher
echo ==================================

REM Kill existing Chrome instances
taskkill /F /IM chrome.exe 2>nul
timeout /t 2 /nobreak >nul

REM Create fresh profile
if exist "%PROFILE_DIR%" rmdir /S /Q "%PROFILE_DIR%"
mkdir "%PROFILE_DIR%"

REM Launch Chrome
echo 🪟 Launching Chrome on Windows...
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" ^
    --remote-debugging-port=%PORT% ^
    --user-data-dir="%PROFILE_DIR%" ^
    --no-first-run ^
    --no-default-browser-check ^
    about:blank

echo ✅ Chrome started on port %PORT%
echo 👉 Please log into the portal manually before running tests
pause
```

### 5.2 Session Manager

**File: `src/runner/session.ts`**

```typescript
import { chromium, Browser, BrowserContext, Page } from 'playwright';
import { logger } from '../utils/logger';
import { SanityConfig } from '../config/sanity.config';

export class SessionManager {
  private browser: Browser | null = null;
  private context: BrowserContext | null = null;
  private page: Page | null = null;

  /**
   * Connect to existing Chrome instance via CDP
   */
  async connect(config: SanityConfig): Promise<void> {
    const cdpUrl = `http://localhost:${config.cdpPort}`;
    
    logger.info(`🔌 Connecting to Chrome at ${cdpUrl}`);

    try {
      // Connect to browser
      this.browser = await chromium.connectOverCDP(cdpUrl, {
        timeout: 10000,
      });

      logger.success('✅ Connected to Chrome');

      // Get or create context
      const contexts = this.browser.contexts();
      
      if (contexts.length === 0) {
        throw new Error('No browser contexts found. Please open Chrome and log in first.');
      }

      this.context = contexts[0];
      logger.info(`📋 Using browser context with ${this.context.pages().length} pages`);

      // Find or create page
      await this.attachToPage(config.portalUrl);

      // Setup context listeners
      await this.setupContextListeners();

    } catch (error) {
      logger.error('❌ Failed to connect to Chrome:', error);
      throw new Error(
        `Cannot connect to Chrome. Ensure Chrome is running with:\n` +
        `  ./scripts/start-chrome.sh ${config.cdpPort}`
      );
    }
  }

  /**
   * Attach to existing portal page or navigate to it
   */
  private async attachToPage(portalUrl: string): Promise<void> {
    if (!this.context) {
      throw new Error('No browser context available');
    }

    const pages = this.context.pages();
    
    // Try to find existing portal page
    const portalPage = pages.find(p => 
      p.url().startsWith(portalUrl) || 
      p.url().includes(new URL(portalUrl).hostname)
    );

    if (portalPage) {
      this.page = portalPage;
      logger.info(`✅ Attached to existing portal page: ${this.page.url()}`);
      
      // Bring page to front
      await this.page.bringToFront();
    } else {
      // Create new page and navigate
      this.page = await this.context.newPage();
      logger.info(`🌐 Navigating to ${portalUrl}`);
      
      await this.page.goto(portalUrl, { 
        waitUntil: 'networkidle',
        timeout: 30000 
      });
    }

    // Wait for page to be fully ready
    await this.page.waitForLoadState('domcontentloaded');
    await this.page.waitForLoadState('load');
  }

  /**
   * Setup context-level event listeners
   */
  private async setupContextListeners(): Promise<void> {
    if (!this.context) return;

    // Listen for new pages (handle popups/new tabs)
    this.context.on('page', (page) => {
      logger.debug(`New page opened: ${page.url()}`);
    });
  }

  /**
   * Validate that session is authenticated
   */
  async validateAuthentication(config: SanityConfig): Promise<boolean> {
    if (!this.page) {
      throw new Error('No page available');
    }

    logger.info('🔐 Validating authentication...');

    try {
      // Multiple authentication checks
      const authChecks = await Promise.all([
        // 1. Check for auth cookies
        this.checkAuthCookies(),
        
        // 2. Check for logged-in UI elements
        this.checkAuthUI(),
        
        // 3. Check localStorage/sessionStorage for auth tokens
        this.checkAuthStorage(),
        
        // 4. Check for login redirect
        this.checkNotOnLoginPage(config),
      ]);

      const passedChecks = authChecks.filter(Boolean).length;
      const totalChecks = authChecks.length;

      logger.debug(`Authentication checks: ${passedChecks}/${totalChecks} passed`);

      // Require at least 2 checks to pass
      const isAuthenticated = passedChecks >= 2;

      if (isAuthenticated) {
        logger.success('✅ Session is authenticated');
        
        // Capture authenticated user info
        await this.captureUserInfo();
        
        return true;
      } else {
        logger.error('❌ Session is NOT authenticated');
        logger.warn('👉 Please log in manually before running tests');
        logger.info(`   Passed ${passedChecks}/${totalChecks} authentication checks`);
        
        return false;
      }

    } catch (error) {
      logger.error('❌ Authentication validation failed:', error);
      return false;
    }
  }

  /**
   * Check for authentication cookies
   */
  private async checkAuthCookies(): Promise<boolean> {
    if (!this.context) return false;

    const cookies = await this.context.cookies();
    const authCookiePatterns = [
      'session',
      'auth',
      'token',
      'jwt',
      'access',
      'sid',
      'PHPSESSID',
      'connect.sid',
    ];

    const hasAuthCookie = cookies.some(cookie => 
      authCookiePatterns.some(pattern => 
        cookie.name.toLowerCase().includes(pattern)
      ) && cookie.value.length > 10
    );

    logger.debug(`Auth cookie check: ${hasAuthCookie}`);
    return hasAuthCookie;
  }

  /**
   * Check for authenticated UI elements
   */
  private async checkAuthUI(): Promise<boolean> {
    if (!this.page) return false;

    const uiSelectors = [
      '[data-testid="user-menu"]',
      '[data-testid="user-avatar"]',
      '.user-menu',
      '.user-avatar',
      '#user-dropdown',
      '[aria-label*="user" i]',
      '[aria-label*="profile" i]',
    ];

    for (const selector of uiSelectors) {
      try {
        const isVisible = await this.page.locator(selector).isVisible({ timeout: 2000 });
        if (isVisible) {
          logger.debug(`Auth UI check: Found ${selector}`);
          return true;
        }
      } catch {
        // Continue to next selector
      }
    }

    logger.debug('Auth UI check: No auth UI elements found');
    return false;
  }

  /**
   * Check for auth tokens in storage
   */
  private async checkAuthStorage(): Promise<boolean> {
    if (!this.page) return false;

    const hasAuthToken = await this.page.evaluate(() => {
      const tokenKeys = [
        'authToken',
        'accessToken',
        'idToken',
        'token',
        'jwt',
        'user',
        'session',
      ];

      // Check localStorage
      for (const key of tokenKeys) {
        if (localStorage.getItem(key)) {
          return true;
        }
      }

      // Check sessionStorage
      for (const key of tokenKeys) {
        if (sessionStorage.getItem(key)) {
          return true;
        }
      }

      return false;
    });

    logger.debug(`Auth storage check: ${hasAuthToken}`);
    return hasAuthToken;
  }

  /**
   * Verify not on login page
   */
  private async checkNotOnLoginPage(config: SanityConfig): Promise<boolean> {
    if (!this.page) return false;

    const currentUrl = this.page.url();
    const loginPatterns = ['/login', '/signin', '/auth', '/sso'];

    const isOnLoginPage = loginPatterns.some(pattern => 
      currentUrl.includes(pattern)
    );

    logger.debug(`Login page check: ${!isOnLoginPage} (URL: ${currentUrl})`);
    return !isOnLoginPage;
  }

  /**
   * Capture authenticated user information
   */
  private async captureUserInfo(): Promise<void> {
    if (!this.page) return;

    try {
      const userInfo = await this.page.evaluate(() => {
        // Try to extract user info from common locations
        const userElement = document.querySelector('[data-user-name], [data-username]');
        const userName = userElement?.textContent?.trim();

        return {
          userName: userName || 'Unknown User',
          url: window.location.href,
          timestamp: new Date().toISOString(),
        };
      });

      logger.info(`👤 Authenticated as: ${userInfo.userName}`);
    } catch (error) {
      logger.debug('Could not capture user info:', error);
    }
  }

  /**
   * Get current page
   */
  getPage(): Page {
    if (!this.page) {
      throw new Error('No page available. Call connect() first.');
    }
    return this.page;
  }

  /**
   * Get browser context
   */
  getContext(): BrowserContext {
    if (!this.context) {
      throw new Error('No context available. Call connect() first.');
    }
    return this.context;
  }

  /**
   * Get browser instance
   */
  getBrowser(): Browser {
    if (!this.browser) {
      throw new Error('No browser available. Call connect() first.');
    }
    return this.browser;
  }

  /**
   * Disconnect from browser (but don't close it)
   */
  async disconnect(): Promise<void> {
    logger.info('🔌 Disconnecting from browser...');
    
    // We don't close the browser since it was started externally
    // Just close our connection
    if (this.browser) {
      await this.browser.close();
      this.browser = null;
      this.context = null;
      this.page = null;
    }

    logger.success('✅ Disconnected');
  }

  /**
   * Capture current session state for debugging
   */
  async captureState(): Promise<SessionState> {
    if (!this.page || !this.context) {
      throw new Error('No active session');
    }

    return {
      url: this.page.url(),
      title: await this.page.title(),
      cookies: await this.context.cookies(),
      localStorage: await this.page.evaluate(() => ({ ...localStorage })),
      sessionStorage: await this.page.evaluate(() => ({ ...sessionStorage })),
      viewport: this.page.viewportSize(),
      userAgent: await this.page.evaluate(() => navigator.userAgent),
    };
  }

  /**
   * Take a screenshot for debugging
   */
  async screenshot(name: string): Promise<string> {
    if (!this.page) {
      throw new Error('No page available');
    }

    const path = `output/debug/${name}-${Date.now()}.png`;
    await this.page.screenshot({ path, fullPage: true });
    return path;
  }
}

export interface SessionState {
  url: string;
  title: string;
  cookies: any[];
  localStorage: Record<string, string>;
  sessionStorage: Record<string, string>;
  viewport: { width: number; height: number } | null;
  userAgent: string;
}
```

-----

## 6. Workflow Framework

### 6.1 Base Workflow Class

**File: `src/workflows/base.workflow.ts`**

```typescript
import { Page } from 'playwright';
import { logger } from '../utils/logger';
import { EvidenceCollector } from '../evidence/collector';
import { ConsoleCheck } from '../checks/console.check';
import { NetworkCheck } from '../checks/network.check';
import { RenderingCheck } from '../checks/rendering.check';

export abstract class BaseWorkflow {
  protected page: Page;
  protected evidence: EvidenceCollector;
  protected consoleCheck: ConsoleCheck;
  protected networkCheck: NetworkCheck;
  protected renderingCheck: RenderingCheck;
  
  protected startTime: number = 0;
  protected endTime: number = 0;
  protected workflowId: string = '';
  
  abstract name: string;
  abstract description: string;
  abstract category: WorkflowCategory;
  abstract priority: WorkflowPriority;

  constructor(page: Page, evidence: EvidenceCollector) {
    this.page = page;
    this.evidence = evidence;
    this.consoleCheck = new ConsoleCheck(page);
    this.networkCheck = new NetworkCheck(page);
    this.renderingCheck = new RenderingCheck(page);
    this.workflowId = `${this.name.toLowerCase().replace(/\s+/g, '-')}-${Date.now()}`;
  }

  /**
   * Execute the workflow
   */
  async execute(): Promise<WorkflowResult> {
    this.startTime = Date.now();
    logger.info(`\n${'='.repeat(70)}`);
    logger.info(`▶️  Executing: ${this.name}`);
    logger.info(`📝 ${this.description}`);
    logger.info(`🏷️  Priority: ${this.priority} | Category: ${this.category}`);
    logger.info(`${'='.repeat(70)}\n`);

    try {
      // Start monitoring
      await this.consoleCheck.startMonitoring();
      await this.networkCheck.startMonitoring();
      await this.renderingCheck.startMonitoring();

      // Start trace recording
      await this.evidence.startTrace(this.workflowId);

      // Navigate to start route
      await this.navigateToStart();

      // Take initial screenshot
      await this.evidence.captureScreenshot(this.workflowId, 'start');

      // Execute workflow steps
      await this.executeSteps();

      // Take final screenshot
      await this.evidence.captureScreenshot(this.workflowId, 'end');

      // Validate success criteria
      await this.validateSuccess();

      // Check for issues
      const consoleErrors = await this.consoleCheck.getErrors();
      const networkErrors = await this.networkCheck.getErrors();
      const renderingIssues = await this.renderingCheck.getIssues();

      this.endTime = Date.now();

      // Stop trace
      const tracePath = await this.evidence.stopTrace(this.workflowId);

      // Determine result
      if (consoleErrors.length > 0 || networkErrors.length > 0) {
        return this.createResult('FAILED', {
          consoleErrors,
          networkErrors,
          renderingIssues,
          tracePath,
        });
      }

      if (renderingIssues.length > 0) {
        logger.warn(`⚠️  ${renderingIssues.length} rendering issues detected`);
      }

      logger.success(`✅ Workflow passed in ${this.getDuration()}ms`);

      return this.createResult('PASSED', {
        renderingIssues,
        tracePath,
      });

    } catch (error) {
      this.endTime = Date.now();
      logger.error(`❌ Workflow failed: ${error}`);
      
      // Capture failure evidence
      await this.evidence.captureFailure(this.workflowId, error as Error);
      
      // Stop trace
      const tracePath = await this.evidence.stopTrace(this.workflowId);

      return this.createResult('FAILED', { 
        error: error as Error,
        tracePath,
      });
    } finally {
      // Stop monitoring
      await this.consoleCheck.stopMonitoring();
      await this.networkCheck.stopMonitoring();
      await this.renderingCheck.stopMonitoring();

      // Cleanup test data
      try {
        await this.cleanup();
      } catch (cleanupError) {
        logger.warn(`⚠️  Cleanup warning:`, cleanupError);
      }
    }
  }

  /**
   * Navigate to workflow start point
   */
  protected abstract navigateToStart(): Promise<void>;

  /**
   * Execute workflow-specific steps
   */
  protected abstract executeSteps(): Promise<void>;

  /**
   * Validate workflow completed successfully
   */
  protected abstract validateSuccess(): Promise<void>;

  /**
   * Clean up test data created during workflow
   */
  protected abstract cleanup(): Promise<void>;

  /**
   * Create workflow result
   */
  private createResult(
    status: WorkflowStatus,
    details?: Partial<WorkflowResult>
  ): WorkflowResult {
    const duration = this.getDuration();

    return {
      workflowId: this.workflowId,
      workflow: this.name,
      status,
      duration,
      timestamp: new Date().toISOString(),
      category: this.category,
      priority: this.priority,
      ...details,
    };
  }

  /**
   * Get workflow duration in milliseconds
   */
  private getDuration(): number {
    return this.endTime - this.startTime;
  }

  /**
   * Helper: Wait for navigation
   */
  protected async waitForNavigation(action: () => Promise<void>): Promise<void> {
    await Promise.all([
      this.page.waitForLoadState('networkidle'),
      action(),
    ]);
  }

  /**
   * Helper: Fill form field safely
   */
  protected async fillField(selector: string, value: string): Promise<void> {
    await this.page.waitForSelector(selector, { state: 'visible' });
    await this.page.fill(selector, value);
    logger.debug(`Filled field ${selector} with: ${value}`);
  }

  /**
   * Helper: Click and wait
   */
  protected async clickAndWait(selector: string, waitForSelector?: string): Promise<void> {
    await this.page.click(selector);
    logger.debug(`Clicked: ${selector}`);
    
    if (waitForSelector) {
      await this.page.waitForSelector(waitForSelector, { state: 'visible' });
      logger.debug(`Waited for: ${waitForSelector}`);
    } else {
      await this.page.waitForLoadState('networkidle');
    }
  }

  /**
   * Helper: Select dropdown option
   */
  protected async selectOption(selector: string, value: string): Promise<void> {
    await this.page.selectOption(selector, value);
    logger.debug(`Selected option ${value} in ${selector}`);
  }

  /**
   * Helper: Wait for element to be visible
   */
  protected async waitForVisible(selector: string, timeout: number = 10000): Promise<void> {
    await this.page.waitForSelector(selector, { state: 'visible', timeout });
  }

  /**
   * Helper: Wait for element to be hidden
   */
  protected async waitForHidden(selector: string, timeout: number = 10000): Promise<void> {
    await this.page.waitForSelector(selector, { state: 'hidden', timeout });
  }

  /**
   * Helper: Assert element exists
   */
  protected async assertElementExists(selector: string, message?: string): Promise<void> {
    const element = await this.page.locator(selector);
    const count = await element.count();
    
    if (count === 0) {
      throw new Error(message || `Element not found: ${selector}`);
    }
  }

  /**
   * Helper: Assert text content
   */
  protected async assertTextContent(
    selector: string, 
    expectedText: string | RegExp
  ): Promise<void> {
    const element = this.page.locator(selector);
    const text = await element.textContent();
    
    if (typeof expectedText === 'string') {
      if (text?.trim() !== expectedText) {
        throw new Error(
          `Text mismatch. Expected: "${expectedText}", Got: "${text}"`
        );
      }
    } else {
      if (!expectedText.test(text || '')) {
        throw new Error(
          `Text doesn't match pattern. Expected: ${expectedText}, Got: "${text}"`
        );
      }
    }
  }

  /**
   * Helper: Take checkpoint screenshot
   */
  protected async checkpoint(name: string): Promise<void> {
    await this.evidence.captureScreenshot(this.workflowId, name);
    logger.debug(`📸 Checkpoint: ${name}`);
  }
}

export enum WorkflowCategory {
  CRITICAL = 'critical',   // Must work for product to function
  CORE = 'core',          // Main features users rely on
  EXTENDED = 'extended',  // Nice-to-have features
}

export enum WorkflowPriority {
  P0 = 'P0', // Blocking - Must pass
  P1 = 'P1', // High - Should pass
  P2 = 'P2', // Medium - Nice to pass
}

export type WorkflowStatus = 'PASSED' | 'FAILED' | 'SKIPPED';

export interface WorkflowResult {
  workflowId: string;
  workflow: string;
  status: WorkflowStatus;
  duration: number;
  timestamp: string;
  category: WorkflowCategory;
  priority: WorkflowPriority;
  error?: Error;
  consoleErrors?: any[];
  networkErrors?: any[];
  renderingIssues?: any[];
  screenshots?: string[];
  tracePath?: string;
}
```

### 6.2 Example Workflow Implementations

**File: `src/workflows/content.create.workflow.ts`**

```typescript
import { BaseWorkflow, WorkflowCategory, WorkflowPriority } from './base.workflow';
import { ROUTES } from '../config/routes';
import { SELECTORS } from '../config/selectors';
import { generateTestId } from '../utils/crypto';

export class ContentCreateWorkflow extends BaseWorkflow {
  name = 'Content Creation Flow';
  description = 'Create a new content item from scratch';
  category = WorkflowCategory.CRITICAL;
  priority = WorkflowPriority.P0;

  private contentId: string = '';
  private contentTitle: string = '';

  protected async navigateToStart(): Promise<void> {
    await this.page.goto(ROUTES.CONTENT_LIST);
    await this.waitForVisible(SELECTORS.CONTENT.CREATE_BUTTON);
  }

  protected async executeSteps(): Promise<void> {
    // Step 1: Click "Create New Content"
    await this.clickAndWait(
      SELECTORS.CONTENT.CREATE_BUTTON,
      SELECTORS.CONTENT.FORM_CONTAINER
    );
    await this.checkpoint('create-form-opened');

    // Step 2: Fill in content details
    this.contentTitle = `Sanity Test Content ${generateTestId()}`;
    
    await this.fillField(SELECTORS.CONTENT.TITLE_INPUT, this.contentTitle);
    await this.fillField(
      SELECTORS.CONTENT.DESCRIPTION_INPUT,
      'This is a test content item created by sanity automation'
    );
    await this.checkpoint('form-filled');

    // Step 3: Select content type
    await this.page.click(SELECTORS.CONTENT.TYPE_DROPDOWN);
    await this.page.click(SELECTORS.CONTENT.TYPE_OPTION_ARTICLE);
    await this.checkpoint('type-selected');

    // Step 4: Add content body
    await this.page.click(SELECTORS.CONTENT.BODY_EDITOR);
    await this.page.keyboard.type('This is the content body for testing purposes.');
    await this.checkpoint('body-added');

    // Step 5: Save as draft
    await this.clickAndWait(
      SELECTORS.CONTENT.SAVE_DRAFT_BUTTON,
      SELECTORS.CONTENT.SUCCESS_MESSAGE
    );
    await this.checkpoint('saved');

    // Step 6: Capture content ID from URL or DOM
    await this.extractContentId();
  }

  protected async validateSuccess(): Promise<void> {
    // Verify success message appears
    const successMsg = await this.page.locator(SELECTORS.CONTENT.SUCCESS_MESSAGE).textContent();
    if (!successMsg?.toLowerCase().includes('saved successfully')) {
      throw new Error(`Expected success message, got: ${successMsg}`);
    }

    // Verify content appears in list
    await this.page.goto(ROUTES.CONTENT_LIST);
    await this.waitForVisible(SELECTORS.CONTENT.LIST_TABLE);
    
    const contentRow = this.page.locator(`text=${this.contentTitle}`);
    
    if (!(await contentRow.isVisible())) {
      throw new Error('Created content not found in content list');
    }

    // Verify content has correct status
    const statusBadge = this.page.locator(
      `${SELECTORS.CONTENT.ROW_BY_TITLE(this.contentTitle)} ${SELECTORS.CONTENT.STATUS_BADGE}`
    );
    const status = await statusBadge.textContent();
    
    if (status?.toLowerCase() !== 'draft') {
      throw new Error(`Expected status 'draft', got '${status}'`);
    }
  }

  protected async cleanup(): Promise<void> {
    if (!this.contentId) {
      logger.warn('⚠️  No content ID to clean up');
      return;
    }

    try {
      // Navigate to content
      await this.page.goto(`${ROUTES.CONTENT_DETAIL}/${this.contentId}`);
      
      // Delete content
      await this.page.click(SELECTORS.CONTENT.MORE_OPTIONS_BUTTON);
      await this.page.click(SELECTORS.CONTENT.DELETE_OPTION);
      await this.page.click(SELECTORS.CONTENT.CONFIRM_DELETE_BUTTON);
      
      // Wait for deletion confirmation
      await this.waitForVisible(SELECTORS.CONTENT.DELETE_SUCCESS_MESSAGE);
      
      logger.info(`🧹 Cleaned up content: ${this.contentId}`);
    } catch (error) {
      logger.error(`❌ Cleanup failed for content ${this.contentId}:`, error);
      throw error; // Re-throw to track cleanup failures
    }
  }

  /**
   * Extract content ID from URL or DOM
   */
  private async extractContentId(): Promise<void> {
    // Method 1: From URL
    const url = this.page.url();
    let match = url.match(/\/content\/([a-zA-Z0-9-_]+)/);
    
    if (match) {
      this.contentId = match[1];
      logger.info(`📝 Content ID from URL: ${this.contentId}`);
      return;
    }

    // Method 2: From data attribute
    try {
      const idAttr = await this.page.getAttribute(
        SELECTORS.CONTENT.FORM_CONTAINER,
        'data-content-id'
      );
      if (idAttr) {
        this.contentId = idAttr;
        logger.info(`📝 Content ID from DOM: ${this.contentId}`);
        return;
      }
    } catch {
      // Continue to next method
    }

    logger.warn('⚠️  Could not extract content ID');
  }
}
```

**File: `src/workflows/dashboard.workflow.ts`**

```typescript
import { BaseWorkflow, WorkflowCategory, WorkflowPriority } from './base.workflow';
import { ROUTES } from '../config/routes';
import { SELECTORS } from '../config/selectors';

export class DashboardWorkflow extends BaseWorkflow {
  name = 'Dashboard Load & Render';
  description = 'Verify dashboard loads correctly with all widgets';
  category = WorkflowCategory.CRITICAL;
  priority = WorkflowPriority.P0;

  protected async navigateToStart(): Promise<void> {
    await this.page.goto(ROUTES.DASHBOARD);
  }

  protected async executeSteps(): Promise<void> {
    // Step 1: Wait for dashboard to load
    await this.waitForVisible(SELECTORS.DASHBOARD.CONTAINER);
    await this.checkpoint('dashboard-loaded');

    // Step 2: Verify all required widgets are present
    const requiredWidgets = [
      SELECTORS.DASHBOARD.STATS_WIDGET,
      SELECTORS.DASHBOARD.RECENT_ACTIVITY,
      SELECTORS.DASHBOARD.QUICK_ACTIONS,
    ];

    for (const widget of requiredWidgets) {
      await this.assertElementExists(widget, `Required widget not found: ${widget}`);
    }
    await this.checkpoint('widgets-verified');

    // Step 3: Verify data is loaded (not just skeleton screens)
    await this.page.waitForFunction(() => {
      const skeletons = document.querySelectorAll('.skeleton, [data-loading="true"]');
      return skeletons.length === 0;
    }, { timeout: 10000 });
    await this.checkpoint('data-loaded');
  }

  protected async validateSuccess(): Promise<void> {
    // Verify page title
    const title = await this.page.title();
    if (!title.toLowerCase().includes('dashboard')) {
      throw new Error(`Expected dashboard title, got: ${title}`);
    }

    // Verify no empty states
    const emptyState = await this.page.locator(SELECTORS.DASHBOARD.EMPTY_STATE).count();
    if (emptyState > 0) {
      throw new Error('Dashboard showing empty state');
    }

    // Verify stats have numeric values
    const statsElements = await this.page.locator(SELECTORS.DASHBOARD.STAT_VALUE).all();
    for (const stat of statsElements) {
      const text = await stat.textContent();
      if (!text || text.trim() === '' || text === '0') {
        logger.warn(`⚠️  Stat widget may be empty: ${text}`);
      }
    }
  }

  protected async cleanup(): Promise<void> {
    // No cleanup needed for dashboard view
  }
}
```

-----

## 7. Validation & Assertion Layer

### 7.1 Console Error Monitor

**File: `src/checks/console.check.ts`**

```typescript
import { Page, ConsoleMessage } from 'playwright';
import { logger } from '../utils/logger';

export class ConsoleCheck {
  private page: Page;
  private errors: ConsoleError[] = [];
  private warnings: ConsoleError[] = [];
  private isMonitoring = false;

  constructor(page: Page) {
    this.page = page;
  }

  async startMonitoring(): Promise<void> {
    if (this.isMonitoring) return;

    this.errors = [];
    this.warnings = [];
    this.isMonitoring = true;

    // Listen to console messages
    this.page.on('console', (msg: ConsoleMessage) => {
      const type = msg.type();
      const text = msg.text();
      const location = msg.location();

      if (type === 'error') {
        // Filter out known non-critical errors
        if (this.shouldIgnoreError(text)) {
          logger.debug(`Ignored console error: ${text}`);
          return;
        }

        this.errors.push({
          type: 'console-error',
          message: text,
          location,
          timestamp: new Date().toISOString(),
          args: msg.args().map(arg => arg.toString()),
        });

        logger.warn(`⚠️  Console error: ${text}`);
      } else if (type === 'warning') {
        if (!this.shouldIgnoreWarning(text)) {
          this.warnings.push({
            type: 'console-warning',
            message: text,
            location,
            timestamp: new Date().toISOString(),
          });
        }
      }
    });

    // Listen to page errors (uncaught exceptions)
    this.page.on('pageerror', (error: Error) => {
      this.errors.push({
        type: 'page-error',
        message: error.message,
        stack: error.stack,
        timestamp: new Date().toISOString(),
      });

      logger.error(`❌ Page error: ${error.message}`);
    });

    logger.debug('Console monitoring started');
  }

  async stopMonitoring(): Promise<void> {
    if (!this.isMonitoring) return;

    this.isMonitoring = false;
    this.page.removeAllListeners('console');
    this.page.removeAllListeners('pageerror');

    logger.debug('Console monitoring stopped');

    if (this.errors.length > 0) {
      logger.warn(`⚠️  Detected ${this.errors.length} console errors`);
    }
  }

  getErrors(): ConsoleError[] {
    return this.errors;
  }

  getWarnings(): ConsoleError[] {
    return this.warnings;
  }

  hasErrors(): boolean {
    return this.errors.length > 0;
  }

  /**
   * Determine if error should be ignored
   */
  private shouldIgnoreError(message: string): boolean {
    const ignoredPatterns = [
      // Browser extension errors
      /Failed to load resource.*extension/i,
      /chrome-extension:/i,
      
      // Common non-critical errors
      /Failed to load resource.*favicon/i,
      /Download the React DevTools/i,
      /Download the Vue DevTools/i,
      
      // Analytics/tracking errors
      /google-analytics/i,
      /gtag/i,
      /ga\.js/i,
      
      // Third-party widgets
      /widget.*failed to load/i,
      
      // Dev mode warnings
      /development mode/i,
    ];

    return ignoredPatterns.some(pattern => pattern.test(message));
  }

  /**
   * Determine if warning should be ignored
   */
  private shouldIgnoreWarning(message: string): boolean {
    const ignoredPatterns = [
      /deprecated/i,
      /React DevTools/i,
      /source map/i,
    ];

    return ignoredPatterns.some(pattern => pattern.test(message));
  }
}

export interface ConsoleError {
  type: string;
  message: string;
  location?: {
    url: string;
    lineNumber: number;
    columnNumber: number;
  };
  stack?: string;
  timestamp: string;
  args?: string[];
}
```

### 7.2 Network Monitor

**File: `src/checks/network.check.ts`**

```typescript
import { Page, Request, Response } from 'playwright';
import { logger } from '../utils/logger';

export class NetworkCheck {
  private page: Page;
  private failedRequests: FailedRequest[] = [];
  private slowRequests: SlowRequest[] = [];
  private isMonitoring = false;
  private slowThreshold = 5000; // 5 seconds

  constructor(page: Page, slowThreshold?: number) {
    this.page = page;
    if (slowThreshold) {
      this.slowThreshold = slowThreshold;
    }
  }

  async startMonitoring(): Promise<void> {
    if (this.isMonitoring) return;

    this.failedRequests = [];
    this.slowRequests = [];
    this.isMonitoring = true;

    // Monitor successful requests for slow ones
    this.page.on('requestfinished', async (request: Request) => {
      const response = await request.response();
      const timing = request.timing();

      if (response) {
        const status = response.status();
        const url = request.url();
        
        // Skip ignored URLs
        if (this.shouldIgnoreRequest(url)) {
          return;
        }

        // Track failed requests (4xx, 5xx)
        if (status >= 400) {
          const body = await this.safeGetResponseBody(response);
          
          this.failedRequests.push({
            url,
            method: request.method(),
            status,
            statusText: response.statusText(),
            headers: response.headers(),
            responseBody: body,
            timestamp: new Date().toISOString(),
          });

          logger.warn(`⚠️  Failed request: ${request.method()} ${url} - ${status}`);
        }

        // Track slow requests
        const duration = timing.responseEnd - timing.requestStart;
        if (duration > this.slowThreshold) {
          this.slowRequests.push({
            url,
            method: request.method(),
            duration,
            timestamp: new Date().toISOString(),
          });

          logger.warn(`⚠️  Slow request (${duration}ms): ${request.method()} ${url}`);
        }
      }
    });

    // Monitor failed requests (network errors)
    this.page.on('requestfailed', (request: Request) => {
      const url = request.url();
      
      if (this.shouldIgnoreRequest(url)) {
        return;
      }

      this.failedRequests.push({
        url,
        method: request.method(),
        failure: request.failure()?.errorText || 'Unknown error',
        timestamp: new Date().toISOString(),
      });

      logger.error(`❌ Request failed: ${request.method()} ${url}`);
    });

    logger.debug('Network monitoring started');
  }

  async stopMonitoring(): Promise<void> {
    if (!this.isMonitoring) return;

    this.isMonitoring = false;
    this.page.removeAllListeners('requestfinished');
    this.page.removeAllListeners('requestfailed');

    logger.debug('Network monitoring stopped');

    if (this.failedRequests.length > 0) {
      logger.warn(`⚠️  Detected ${this.failedRequests.length} failed requests`);
    }

    if (this.slowRequests.length > 0) {
      logger.warn(`⚠️  Detected ${this.slowRequests.length} slow requests`);
    }
  }

  getErrors(): FailedRequest[] {
    return this.failedRequests;
  }

  getSlowRequests(): SlowRequest[] {
    return this.slowRequests;
  }

  hasErrors(): boolean {
    return this.failedRequests.length > 0;
  }

  /**
   * Safely get response body
   */
  private async safeGetResponseBody(response: Response): Promise<string | null> {
    try {
      const body = await response.text();
      return body.substring(0, 500); // Limit to first 500 chars
    } catch {
      return null;
    }
  }

  /**
   * Determine if request should be ignored
   */
  private shouldIgnoreRequest(url: string): boolean {
    const ignoredPatterns = [
      // Analytics
      /google-analytics\.com/,
      /googletagmanager\.com/,
      /analytics\.google\.com/,
      
      // Ads
      /doubleclick\.net/,
      /googlesyndication\.com/,
      
      // Social media widgets
      /facebook\.com\/plugins/,
      /platform\.twitter\.com/,
      
      // CDNs for external resources
      /fonts\.googleapis\.com/,
      /fonts\.gstatic\.com/,
      
      // Browser extensions
      /chrome-extension:/,
    ];

    return ignoredPatterns.some(pattern => pattern.test(url));
  }
}

export interface FailedRequest {
  url: string;
  method: string;
  status?: number;
  statusText?: string;
  headers?: Record<string, string>;
  responseBody?: string | null;
  failure?: string;
  timestamp: string;
}

export interface SlowRequest {
  url: string;
  method: string;
  duration: number;
  timestamp: string;
}
```

### 7.3 Rendering Check

**File: `src/checks/rendering.check.ts`**

```typescript
import { Page } from 'playwright';
import { logger } from '../utils/logger';

export class RenderingCheck {
  private page: Page;
  private issues: RenderingIssue[] = [];
  private isMonitoring = false;

  constructor(page: Page) {
    this.page = page;
  }

  async startMonitoring(): Promise<void> {
    this.isMonitoring = true;
    this.issues = [];
    logger.debug('Rendering monitoring started');
  }

  async stopMonitoring(): Promise<void> {
    this.isMonitoring = false;
    logger.debug('Rendering monitoring stopped');
  }

  /**
   * Check for layout shifts
   */
  async checkLayoutShift(): Promise<number> {
    const cls = await this.page.evaluate(() => {
      return new Promise<number>((resolve) => {
        let clsScore = 0;

        const observer = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if ((entry as any).hadRecentInput) continue;
            clsScore += (entry as any).value;
          }
        });

        observer.observe({ type: 'layout-shift', buffered: true });

        setTimeout(() => {
          observer.disconnect();
          resolve(clsScore);
        }, 100);
      });
    });

    if (cls > 0.1) {
      this.issues.push({
        type: 'layout-shift',
        message: `High Cumulative Layout Shift detecte
```